# Copyright 2020 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
"""
Functionality for reading and writing AASX files according to "Details of the Asset Administration Shell Part 1 V2.0",
section 7.

The AASX file format is built upon the Open Packaging Conventions (OPC; ECMA 376-2). We use the `pyecma376_2` library
for low level OPC reading and writing. It currently supports all required features except for embedded digital
signatures.

Writing and reading of AASX packages is performed through the AASXReader and AASXWriter classes. Each instance of these
classes wraps an existing AASX file resp. a file to be created and allows to read/write the included AAS objects
into/form object stores. For handling of embedded supplementary files, this module provides the
`AbstractSupplementaryFileContainer` class interface and the `DictSupplementaryFileContainer` implementation.
"""

import abc
import hashlib
import io
import itertools
import logging
import os
import re
from typing import Dict, Tuple, IO, Union, List, Set, Optional, Iterable, Iterator

from .xml import read_aas_xml_file, write_aas_xml_file
from .. import model
from .json import read_aas_json_file, write_aas_json_file
import pyecma376_2
from ..util import traversal

logger = logging.getLogger(__name__)

RELATIONSHIP_TYPE_AASX_ORIGIN = "http://www.admin-shell.io/aasx/relationships/aasx-origin"
RELATIONSHIP_TYPE_AAS_SPEC = "http://www.admin-shell.io/aasx/relationships/aas-spec"
RELATIONSHIP_TYPE_AAS_SPEC_SPLIT = "http://www.admin-shell.io/aasx/relationships/aas-spec-split"
RELATIONSHIP_TYPE_AAS_SUPL = "http://www.admin-shell.io/aasx/relationships/aas-suppl"


class AASXReader:
    """
    An AASXReader wraps an existing AASX package file to allow reading its contents and metadata.

    Basic usage:

        objects = DictObjectStore()
        files = DictSupplementaryFileContainer()
        with AASXReader("filename.aasx") as reader:
            meta_data = reader.get_core_properties()
            reader.read_into(objects, files)
    """
    def __init__(self, file: Union[os.PathLike, str, IO]):
        """
        Open an AASX reader for the given filename or file handle

        The given file is opened as OPC ZIP package. Make sure to call `AASXReader.close()` after reading the file
        contents to close the underlying ZIP file reader. You may also use the AASXReader as a context manager to ensure
        closing under any circumstances.

        :param file: A filename, file path or an open file-like object in binary mode
        :raises ValueError: If the file is not a valid OPC zip package
        """
        try:
            logger.debug("Opening {} as AASX pacakge for reading ...".format(file))
            self.reader = pyecma376_2.ZipPackageReader(file)
        except Exception as e:
            raise ValueError("{} is not a valid ECMA376-2 (OPC) file".format(file)) from e

    def get_core_properties(self) -> pyecma376_2.OPCCoreProperties:
        """
        Retrieve the OPC Core Properties (meta data) of the AASX package file.

        If no meta data is provided in the package file, an emtpy OPCCoreProperties object is returned.

        :return: The AASX package's meta data
        """
        return self.reader.get_core_properties()

    def get_thumbnail(self) -> Optional[bytes]:
        """
        Retrieve the packages thumbnail image

        The thumbnail image file is read into memory and returned as bytes object. You may use some python image library
        for further processing or conversion, e.g. `pillow`:

            import io
            from PIL import Image
            thumbnail = Image.open(io.BytesIO(reader.get_thumbnail()))

        :return: The AASX package thumbnail's file contents or None if no thumbnail is provided
        """
        try:
            thumbnail_part = self.reader.get_related_parts_by_type()[pyecma376_2.RELATIONSHIP_TYPE_THUMBNAIL][0]
        except IndexError:
            return None

        with self.reader.open_part(thumbnail_part) as p:
            return p.read()

    def read_into(self, object_store: model.AbstractObjectStore,
                  file_store: "AbstractSupplementaryFileContainer",
                  override_existing: bool = False) -> Set[model.Identifier]:
        """
        Read the contents of the AASX package and add them into a given ObjectStore

        This function does the main job of reading the AASX file's contents. It traverses the relationships within the
        package to find AAS JSON or XML parts, parses them and adds the contained AAS objects into the provided
        `object_store`. While doing so, it searches all parsed Submodels for File objects to extract the supplementary
        files. The referenced supplementary files are added to the given `file_store` and the File objects' values are
        updated with the absolute name of the supplementary file to allow for robust resolution the file within the
        `file_store` later.

        :param object_store: An ObjectStore to add the AAS objects from the AASX file to
        :param file_store: A SupplementaryFileContainer to add the embedded supplementary files to
        :param override_existing: If True, existing objects in the object store are overridden with objects from the
            AASX that have the same Identifer. Default behavior is to skip those objects from the AASX.
        :return: A set of the Identifiers of all Identifiable objects parsed from the AASX file
        """
        # Find AASX-Origin part
        core_rels = self.reader.get_related_parts_by_type()
        try:
            aasx_origin_part = core_rels[RELATIONSHIP_TYPE_AASX_ORIGIN][0]
        except IndexError as e:
            raise ValueError("Not a valid AASX file: aasx-origin Relationship is missing.") from e

        read_identifiables: Set[model.Identifier] = set()

        # Iterate AAS files
        for aas_part in self.reader.get_related_parts_by_type(aasx_origin_part)[
                RELATIONSHIP_TYPE_AAS_SPEC]:
            self._read_aas_part_into(aas_part, object_store, file_store, read_identifiables, override_existing)

            # Iterate split parts of AAS file
            for split_part in self.reader.get_related_parts_by_type(aas_part)[
                    RELATIONSHIP_TYPE_AAS_SPEC_SPLIT]:
                self._read_aas_part_into(split_part, object_store, file_store, read_identifiables, override_existing)

        return read_identifiables

    def close(self) -> None:
        """
        Close the AASXReader and the underlying OPC / ZIP file readers. Must be called after reading the file.
        """
        self.reader.close()

    def __enter__(self) -> "AASXReader":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _read_aas_part_into(self, part_name: str,
                            object_store: model.AbstractObjectStore,
                            file_store: "AbstractSupplementaryFileContainer",
                            read_identifiables: Set[model.Identifier],
                            override_existing: bool) -> None:
        """
        Helper function for `read_into()` to read and process the contents of an AAS-spec part of the AASX file.

        This method primarily checks for duplicate objects. It uses `_parse_aas_parse()` to do the actual parsing and
        `_collect_supplementary_files()` for supplementary file processing of non-duplicate objects.

        :param part_name: The OPC part name to read
        :param object_store: An ObjectStore to add the AAS objects from the AASX file to
        :param file_store: A SupplementaryFileContainer to add the embedded supplementary files to, which are reference
            from a File object of this part
        :param read_identifiables: A set of Identifiers of objects which have already been read. New objects'
            Identifiers are added to this set. Objects with already known Identifiers are skipped silently.
        :param override_existing: If True, existing objects in the object store are overridden with objects from the
            AASX that have the same Identifer. Default behavior is to skip those objects from the AASX.
        """
        for obj in self._parse_aas_part(part_name):
            if obj.identification in read_identifiables:
                continue
            if obj.identification in object_store:
                if override_existing:
                    logger.info("Overriding existing object in  ObjectStore with {} ...".format(obj))
                    object_store.discard(obj)
                else:
                    logger.warning("Skipping {}, since an object with the same id is already contained in the "
                                   "ObjectStore".format(obj))
                    continue
            object_store.add(obj)
            read_identifiables.add(obj.identification)
            if isinstance(obj, model.Submodel):
                self._collect_supplementary_files(part_name, obj, file_store)

    def _parse_aas_part(self, part_name: str) -> model.DictObjectStore:
        """
        Helper function to parse the AAS objects from a single JSON or XML part of the AASX package.

        This method chooses and calls the correct parser.

        :param part_name: The OPC part name of the part to be parsed
        :return: A DictObjectStore containing the parsed AAS objects
        """
        content_type = self.reader.get_content_type(part_name)
        extension = part_name.split("/")[-1].split(".")[-1]
        if content_type.split(";")[0] in ("text/xml", "application/xml") or content_type == "" and extension == "xml":
            logger.debug("Parsing AAS objects from XML stream in OPC part {} ...".format(part_name))
            with self.reader.open_part(part_name) as p:
                return read_aas_xml_file(p)
        elif content_type.split(";")[0] in ("text/json", "application/json") \
                or content_type == "" and extension == "json":
            logger.debug("Parsing AAS objects from JSON stream in OPC part {} ...".format(part_name))
            with self.reader.open_part(part_name) as p:
                return read_aas_json_file(io.TextIOWrapper(p, encoding='utf-8-sig'))
        else:
            logger.error("Could not determine part format of AASX part {} (Content Type: {}, extension: {}"
                         .format(part_name, content_type, extension))
            return model.DictObjectStore()

    def _collect_supplementary_files(self, part_name: str, submodel: model.Submodel,
                                     file_store: "AbstractSupplementaryFileContainer") -> None:
        """
        Helper function to search File objects within a single parsed Submodel, extract the referenced supplementary
        files and update the File object's values with the absolute path.

        :param part_name: The OPC part name of the part the submodel has been parsed from. This is used to resolve
            relative file paths.
        :param submodel: The Submodel to process
        :param file_store: The SupplementaryFileContainer to add the extracted supplementary files to
        """
        for element in traversal.walk_submodel(submodel):
            if isinstance(element, model.File):
                if element.value is None:
                    continue
                # Only absolute-path references and relative-path URI references (see RFC 3986, sec. 4.2) are considered
                # to refer to files within the AASX package. Thus, we must skip all other types of URIs (esp. absolute
                # URIs and network-path references)
                if element.value.startswith('//') or ':' in element.value.split('/')[0]:
                    logger.info("Skipping supplementary file %s, since it seems to be an absolute URI or network-path "
                                "URI reference", element.value)
                    continue
                absolute_name = pyecma376_2.package_model.part_realpath(element.value, part_name)
                logger.debug("Reading supplementary file {} from AASX package ...".format(absolute_name))
                with self.reader.open_part(absolute_name) as p:
                    final_name = file_store.add_file(absolute_name, p, self.reader.get_content_type(absolute_name))
                element.value = final_name


class AASXWriter:
    """
    An AASXWriter wraps a new AASX package file to write its contents to it piece by piece.

    Basic usage:

        # object_store and file_store are expected to be given (e.g. some storage backend or previously created data)
        cp = OPCCoreProperties()
        cp.creator = "ACPLT"
        cp.created = datetime.datetime.now()

        with AASXWriter("filename.aasx") as writer:
            writer.write_aas(Identifier("https://acplt.org/AssetAdministrationShell", IdentifierType.IRI),
                             object_store,
                             file_store)
            writer.write_aas(Identifier("https://acplt.org/AssetAdministrationShell2", IdentifierType.IRI),
                             object_store,
                             file_store)
            writer.write_core_properties(cp)

    Attention: The AASXWriter must always be closed using the close() method or its context manager functionality (as
    shown above). Otherwise the resulting AASX file will lack important data structures and will not be readable.
    """
    AASX_ORIGIN_PART_NAME = "/aasx/aasx-origin"

    def __init__(self, file: Union[os.PathLike, str, IO]):
        """
        Create a new AASX package in the given file and open the AASXWriter to add contents to the package.

        Make sure to call `AASXWriter.close()` after writing all contents to write the aas-spec relationships for all
        AAS parts to the file and close the underlying ZIP file writer. You may also use the AASXWriter as a context
        manager to ensure closing under any circumstances.

        :param file: filename, path, or binary file handle opened for writing
        """
        # names of aas-spec parts, used by `_write_aasx_origin_relationships()`
        self._aas_part_names: List[str] = []
        # name of the thumbnail part (if any)
        self._thumbnail_part: Optional[str] = None
        # name of the core properties part (if any)
        self._properties_part: Optional[str] = None
        # names and hashes of all supplementary file parts that have already been written
        self._supplementary_part_names: Dict[str, Optional[bytes]] = {}
        self._aas_name_friendlyfier = NameFriendlyfier()

        # Open OPC package writer
        self.writer = pyecma376_2.ZipPackageWriter(file)

        # Create AASX origin part
        logger.debug("Creating AASX origin part in AASX package ...")
        p = self.writer.open_part(self.AASX_ORIGIN_PART_NAME, "text/plain")
        p.close()

    def write_aas(self,
                  aas_id: model.Identifier,
                  object_store: model.AbstractObjectStore,
                  file_store: "AbstractSupplementaryFileContainer",
                  write_json: bool = False,
                  submodel_split_parts: bool = True) -> None:
        """
        Convenience method to add an Asset Administration Shell with all included and referenced objects to the AASX
        package according to the part name conventions from DotAAS.

        This method takes the AAS's Identifier (as `aas_id`) to retrieve it from the given object_store. References to
        the Asset, ConceptDescriptions and Submodels are also resolved using the object_store. All of these objects are
        written to aas-spec parts in the AASX package, follwing the conventions presented in "Details of the Asset
        Administration Shell". For each Submodel, a aas-spec-split part is used. Supplementary files which are
        referenced by a File object in any of the Submodels, are also added to the AASX package.

        Internally, this method uses `write_aas_objects()` to write the individual AASX parts for the AAS and each
        submodel.

        :param aas_id: Identifier of the AAS to be added to the AASX file
        :param object_store: ObjectStore to retrieve the Identifiable AAS objects (AAS, Asset, ConceptDescriptions and
            Submodels) from
        :param file_store: SupplementaryFileContainer to retrieve supplementary files from, which are referenced by File
            objects
        :param write_json:  If True, JSON parts are created for the AAS and each submodel in the AASX package file
            instead of XML parts. Defaults to False.
        :param submodel_split_parts: If True (default), submodels are written to separate AASX parts instead of being
            included in the AAS part with in the AASX package.
        """
        aas_friendly_name = self._aas_name_friendlyfier.get_friendly_name(aas_id)
        aas_part_name = "/aasx/{0}/{0}.aas.{1}".format(aas_friendly_name, "json" if write_json else "xml")

        aas = object_store.get_identifiable(aas_id)
        if not isinstance(aas, model.AssetAdministrationShell):
            raise ValueError(f"Identifier does not belong to an AssetAdminstrationShell object but to {aas!r}")

        objects_to_be_written: Set[model.Identifier] = {aas.identification}

        # Add referenced ConceptDescriptions to the AAS part

        # Write submodels: Either create a split part for each of them or otherwise add them to objects_to_be_written
        aas_split_part_names: List[str] = []
        if submodel_split_parts:
            # Create a AAS split part for each (available) submodel of the AAS
            aas_friendlyfier = NameFriendlyfier()
            for submodel_ref in aas.submodel:
                submodel_identification = submodel_ref.get_identifier()
                submodel_friendly_name = aas_friendlyfier.get_friendly_name(submodel_identification)
                submodel_part_name = "/aasx/{0}/{1}/{1}.submodel.{2}".format(aas_friendly_name, submodel_friendly_name,
                                                                             "json" if write_json else "xml")
                self.write_aas_objects(submodel_part_name, [submodel_identification], object_store, file_store,
                                       write_json, split_part=True)
                aas_split_part_names.append(submodel_part_name)
        else:
            for submodel_ref in aas.submodel:
                objects_to_be_written.add(submodel_ref.get_identifier())

        # Write AAS part
        logger.debug("Writing AAS {} to part {} in AASX package ...".format(aas.identification, aas_part_name))
        self.write_aas_objects(aas_part_name, objects_to_be_written, object_store, file_store, write_json,
                               split_part=False,
                               additional_relationships=(pyecma376_2.OPCRelationship("r{}".format(i),
                                                                                     RELATIONSHIP_TYPE_AAS_SPEC_SPLIT,
                                                                                     submodel_part_name,
                                                                                     pyecma376_2.OPCTargetMode.INTERNAL)
                                                         for i, submodel_part_name in enumerate(aas_split_part_names)))

    def write_aas_objects(self,
                          part_name: str,
                          object_ids: Iterable[model.Identifier],
                          object_store: model.AbstractObjectStore,
                          file_store: "AbstractSupplementaryFileContainer",
                          write_json: bool = False,
                          split_part: bool = False,
                          additional_relationships: Iterable[pyecma376_2.OPCRelationship] = ()) -> None:
        """
        Write a defined list of AAS objects to an XML or JSON part in the AASX package and append the referenced
        supplementary files to the package.

        This method takes the AAS's Identifier (as `aas_id`) to retrieve it from the given object_store. If the list
        of written objects includes Submodel objects, Supplementary files which are referenced by File objects within
        those submodels, are also added to the AASX package.

        You must make sure to call this method only once per unique `part_name` on a single package instance.

        :param part_name: Name of the Part within the AASX package to write the files to. Must be a valid ECMA376-2
            part name and unique within the package. The extension of the part should match the data format (i.e.
            '.json' if `write_json` else '.xml').
        :param object_ids: A list of identifiers of the objects to be written to the AASX package. Only these
            Identifiable objects (and included Referable objects) are written to the package.
        :param object_store: The objects store to retrieve the Identifable objects from
        :param file_store: The SupplementaryFileContainer to retrieve supplementary files from (if there are any `File`
            objects within the written objects.
        :param write_json: If True, the part is written as a JSON file instead of an XML file. Defaults to False.
        :param split_part: If True, no aas-spec relationship is added from the aasx-origin to this part. You must make
            sure to reference it via a aas-spec-split relationship from another aas-spec part
        :param additional_relationships: Optional OPC/ECMA376 relationships which should originate at the AAS object
            part to be written, in addition to the aas-suppl relationships which are created automatically.
        """
        logger.debug("Writing AASX part {} with AAS objects ...".format(part_name))

        objects: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        supplementary_files: List[str] = []

        # Retrieve objects and scan for referenced supplementary files
        for identifier in object_ids:
            try:
                the_object = object_store.get_identifiable(identifier)
            except KeyError:
                logger.error("Could not find object {} in ObjectStore".format(identifier))
                continue
            objects.add(the_object)
            if isinstance(the_object, model.Submodel):
                for element in traversal.walk_submodel(the_object):
                    if isinstance(element, model.File):
                        file_name = element.value
                        # Skip File objects with empty value URI references that are considered to be no local file
                        # (absolute URIs or network-path URI references)
                        if file_name is None or file_name.startswith('//') or ':' in file_name.split('/')[0]:
                            continue
                        supplementary_files.append(file_name)

        # Add aas-spec relationship
        if not split_part:
            self._aas_part_names.append(part_name)

        # Write part
        with self.writer.open_part(part_name, "application/json" if write_json else "application/xml") as p:
            if write_json:
                write_aas_json_file(io.TextIOWrapper(p, encoding='utf-8'), objects)
            else:
                write_aas_xml_file(p, objects)

        # Write submodel's supplementary files to AASX file
        supplementary_file_names = []
        for file_name in supplementary_files:
            try:
                content_type = file_store.get_content_type(file_name)
                hash = file_store.get_sha256(file_name)
            except KeyError:
                logger.warning("Could not find file {} in file store.".format(file_name))
                continue
            # Check if this supplementary file has already been written to the AASX package or has a name conflict
            if self._supplementary_part_names.get(file_name) == hash:
                continue
            elif file_name in self._supplementary_part_names:
                logger.error("Trying to write supplementary file {} to AASX twice with different contents"
                             .format(file_name))
            logger.debug("Writing supplementary file {} to AASX package ...".format(file_name))
            with self.writer.open_part(file_name, content_type) as p:
                file_store.write_file(file_name, p)
            supplementary_file_names.append(pyecma376_2.package_model.normalize_part_name(file_name))
            self._supplementary_part_names[file_name] = hash

        # Add relationships from submodel to supplementary parts
        logger.debug("Writing aas-suppl relationships for AAS object part {} to AASX package ...".format(part_name))
        self.writer.write_relationships(
            itertools.chain(
                (pyecma376_2.OPCRelationship("r{}".format(i),
                                             RELATIONSHIP_TYPE_AAS_SUPL,
                                             submodel_file_name,
                                             pyecma376_2.OPCTargetMode.INTERNAL)
                 for i, submodel_file_name in enumerate(supplementary_file_names)),
                additional_relationships),
            part_name)

    def write_core_properties(self, core_properties: pyecma376_2.OPCCoreProperties):
        """
        Write OPC Core Properties (meta data) to the AASX package file.

        Attention: This method may only be called once for each AASXWriter!

        :param core_properties: The OPCCoreProperties object with the meta data to be written to the package file
        """
        if self._properties_part is not None:
            raise RuntimeError("Core Properties have already been written.")
        logger.debug("Writing core properties to AASX package ...")
        with self.writer.open_part(pyecma376_2.DEFAULT_CORE_PROPERTIES_NAME, "application/xml") as p:
            core_properties.write_xml(p)
        self._properties_part = pyecma376_2.DEFAULT_CORE_PROPERTIES_NAME

    def write_thumbnail(self, name: str, data: bytearray, content_type: str):
        """
        Write an image file as thumbnail image to the AASX package.

        Attention: This method may only be called once for each AASXWriter!

        :param name: The OPC part name of the thumbnail part. Should not contain '/' or URI-encoded '/' or '\'.
        :param data: The image file's binary contents to be written
        :param content_type: OPC content type (MIME type) of the image file
        """
        if self._thumbnail_part is not None:
            raise RuntimeError("package thumbnail has already been written to {}.".format(self._thumbnail_part))
        with self.writer.open_part(name, content_type) as p:
            p.write(data)
        self._thumbnail_part = name

    def close(self):
        """
        Write relationships for all data files to package and close underlying OPC package and ZIP file.
        """
        self._write_aasx_origin_relationships()
        self._write_package_relationships()
        self.writer.close()

    def __enter__(self) -> "AASXWriter":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _write_aasx_origin_relationships(self):
        """
        Helper function to write aas-spec relationships of the aasx-origin part.

        This method uses the list of aas-spec parts in `_aas_part_names`. It should be called just before closing the
        file to make sure all aas-spec parts of the package have already been written.
        """
        # Add relationships from AASX-origin part to AAS parts
        logger.debug("Writing aas-spec relationships to AASX package ...")
        self.writer.write_relationships(
            (pyecma376_2.OPCRelationship("r{}".format(i), RELATIONSHIP_TYPE_AAS_SPEC,
                                         aas_part_name,
                                         pyecma376_2.OPCTargetMode.INTERNAL)
             for i, aas_part_name in enumerate(self._aas_part_names)),
            self.AASX_ORIGIN_PART_NAME)

    def _write_package_relationships(self):
        """
        Helper function to write package (root) relationships to the OPC package.

        This method must be called just before closing the package file to make sure we write exactly the correct
        relationships:
        * aasx-origin (always)
        * core-properties (if core properties have been added)
        * thumbnail (if thumbnail part has been added)
        """
        logger.debug("Writing package relationships to AASX package ...")
        package_relationships: List[pyecma376_2.OPCRelationship] = [
            pyecma376_2.OPCRelationship("r1", RELATIONSHIP_TYPE_AASX_ORIGIN,
                                        self.AASX_ORIGIN_PART_NAME,
                                        pyecma376_2.OPCTargetMode.INTERNAL),
        ]
        if self._properties_part is not None:
            package_relationships.append(pyecma376_2.OPCRelationship(
                "r2", pyecma376_2.RELATIONSHIP_TYPE_CORE_PROPERTIES, self._properties_part,
                pyecma376_2.OPCTargetMode.INTERNAL))
        if self._thumbnail_part is not None:
            package_relationships.append(pyecma376_2.OPCRelationship(
                "r3", pyecma376_2.RELATIONSHIP_TYPE_THUMBNAIL, self._thumbnail_part,
                pyecma376_2.OPCTargetMode.INTERNAL))
        self.writer.write_relationships(package_relationships)


class NameFriendlyfier:
    """
    A simple helper class to create unique "AAS friendly names" according to DotAAS, section 7.6.

    Objects of this class store the already created friendly names to avoid name collisions within one set of names.
    """
    RE_NON_ALPHANUMERICAL = re.compile(r"[^a-zA-Z0-9]")

    def __init__(self) -> None:
        self.issued_names: Set[str] = set()

    def get_friendly_name(self, identifier: model.Identifier):
        """
        Generate a friendly name from an AAS identifier.

        According to section 7.6 of "Details of the Asset Administration Shell", all non-alphanumerical characters are
        replaced with underscores. We also replace all non-ASCII characters to generate valid URIs as the result.
        If this replacement results in a collision with a previously generated friendly name of this NameFriendlifier,
        a number is appended with underscore to the friendly name. Example

            >>> friendlyfier = NameFriendlyfier()
            >>> friendlyfier.get_friendly_name(model.Identifier("http://example.com/AAS-a", model.IdentifierType.IRI))
            "http___example_com_AAS_a"
            >>> friendlyfier.get_friendly_name(model.Identifier("http://example.com/AAS+a", model.IdentifierType.IRI))
            "http___example_com_AAS_a_1"

        """
        # friendlify name
        raw_name = self.RE_NON_ALPHANUMERICAL.sub('_', identifier.id)

        # Unify name (avoid collisions)
        amended_name = raw_name
        i = 1
        while amended_name in self.issued_names:
            amended_name = "{}_{}".format(raw_name, i)
            i += 1

        self.issued_names.add(amended_name)
        return amended_name


class AbstractSupplementaryFileContainer(metaclass=abc.ABCMeta):
    """
    Abstract interface for containers of supplementary files for AASs.

    Supplementary files may be PDF files or other binary or textual files, referenced in a File object of an AAS by
    their name. They are used to provide associated documents without embedding their contents (as Blob object) in the
    AAS.

    A SupplementaryFileContainer keeps track of the name and content_type (MIME type) for each file. Additionally it
    allows to resolve name conflicts by comparing the files' contents and providing an alternative name for a dissimilar
    new file. It also provides each files sha256 hash sum to allow name conflict checking in other classes (e.g. when
    writing AASX files).
    """
    @abc.abstractmethod
    def add_file(self, name: str, file: IO[bytes], content_type: str) -> str:
        """
        Add a new file to the SupplementaryFileContainer and resolve name conflicts.

        The file contents must be provided as a binary file-like object to be read by the SupplementaryFileContainer.
        If the container already contains an equally named file, the content_type and file contents are compared (using
        a hash sum). In case of dissimilar files, a new unique name for the new file is computed and returned. It should
        be used to update in the File object of the AAS.

        :param name: The file's proposed name. Should start with a '/'. Should not contain URI-encoded '/' or '\'
        :param file: A binary file-like opened for reading the file contents
        :param content_type: The file's content_type
        :return: The file name as stored in the SupplementaryFileContainer. Typically `name` or a modified version of
            `name` to resolve conflicts.
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_content_type(self, name: str) -> str:
        """
        Get a stored file's content_type.

        :param name: file name of questioned file
        :return: The file's content_type
        :raises KeyError: If no file with this name is stored
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_sha256(self, name: str) -> bytes:
        """
        Get a stored file content's sha256 hash sum.

        This may be used by other classes (e.g. the AASXWriter) to check for name conflicts.

        :param name: file name of questioned file
        :return: The file content's sha256 hash sum
        :raises KeyError: If no file with this name is stored
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def write_file(self, name: str, file: IO[bytes]) -> None:
        """
        Retrieve a stored file's contents by writing them into a binary writable file-like object.

        :param name: file name of questioned file
        :param file: A binary file-like object with write() method to write the file contents into
        :raises KeyError: If no file with this name is stored
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def __contains__(self, item: str) -> bool:
        """
        Check if a file with the given name is stored in this SupplementaryFileContainer.
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def __iter__(self) -> Iterator[str]:
        """
        Return an iterator over all file names stored in this SupplementaryFileContainer.
        """
        pass  # pragma: no cover


class DictSupplementaryFileContainer(AbstractSupplementaryFileContainer):
    """
    SupplementaryFileContainer implementation using a dict to store the file contents in-memory.
    """
    def __init__(self):
        # Stores the files' contents, identified by their sha256 hash
        self._store: Dict[bytes, bytes] = {}
        # Maps file names to (sha256, content_type)
        self._name_map: Dict[str, Tuple[bytes, str]] = {}

    def add_file(self, name: str, file: IO[bytes], content_type: str) -> str:
        data = file.read()
        hash = hashlib.sha256(data).digest()
        if hash not in self._store:
            self._store[hash] = data
        name_map_data = (hash, content_type)
        new_name = name
        i = 1
        while True:
            if new_name not in self._name_map:
                self._name_map[new_name] = name_map_data
                return new_name
            elif self._name_map[new_name] == name_map_data:
                return new_name
            new_name = self._append_counter(name, i)
            i += 1

    @staticmethod
    def _append_counter(name: str, i: int) -> str:
        split1 = name.split('/')
        split2 = split1[-1].split('.')
        index = -2 if len(split2) > 1 else -1
        new_basename = "{}_{:04d}".format(split2[index], i)
        split2[index] = new_basename
        split1[-1] = ".".join(split2)
        return "/".join(split1)

    def get_content_type(self, name: str) -> str:
        return self._name_map[name][1]

    def get_sha256(self, name: str) -> bytes:
        return self._name_map[name][0]

    def write_file(self, name: str, file: IO[bytes]) -> None:
        file.write(self._store[self._name_map[name][0]])

    def __contains__(self, item: object) -> bool:
        return item in self._name_map

    def __iter__(self) -> Iterator[str]:
        return iter(self._name_map)
