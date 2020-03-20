# Copyright 2019 PyI40AAS Contributors
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
TODO
"""
import abc
import logging
import os
import re
from typing import Dict, Tuple, IO, Union, List, Set, Iterable

from .. import model
from .json.json_deserialization import read_json_aas_file
from .json.json_serialization import write_aas_json_file
import pyecma376_2
from ..util import traversal

logger = logging.getLogger(__name__)


# TODO allow reading thumbnail image
# TODO somehow get core properties
def read_aasx(file: Union[os.PathLike, str, IO],
              object_store: model.AbstractObjectStore,
              file_store: "AbstractSupplementaryFileContainer") -> Set[model.Identifier]:
    """
    TODO
    :param file: AASX file to read (filename or file-like object)
    :param object_store: An ObjectStore to add the read AAS objects into
    :param file_store: A SupplementaryFileContainer to add the supplementary files included in the AASX package to
    :return: List of read AssetAdministrationShells' Identifiers
    """
    # Open file as OPC package file
    try:
        logger.debug("Opening {} as AASX pacakge for reading ...".format(file))
        reader = pyecma376_2.ZipPackageReader(file)
    except Exception as e:
        raise ValueError("{} is not a valid ECMA376-2 (OPC) file".format(file)) from e

    read_identifiables: Set[model.Identifier] = set()

    with reader:
        # Find AASX-Origin part
        core_rels = reader.get_related_parts_by_type()
        try:
            aasx_origin_part = core_rels["http://www.admin-shell.io/aasx/relationships/aasx-origin"][0]
        except IndexError as e:
            raise ValueError("{} is not a valid AASX file: aasx-origin Relationship is missing.".format(file)) \
                from e

        # Iterate AAS files
        for aas_part in reader.get_related_parts_by_type(aasx_origin_part)[
                "http://www.admin-shell.io/aasx/relationships/aas-spec"]:
            with reader.open_part(aas_part) as aas_file:
                part_objects = _parse_aas_part(aas_part, reader.get_content_type(aas_part), aas_file)
            for obj in part_objects:
                if obj.identification in read_identifiables:
                    continue
                if obj.identification not in object_store:
                    object_store.add(obj)
                    read_identifiables.add(obj.identification)
                else:
                    logger.warning("Skipping {}, since an object with the same id is already contained in the "
                                   "ObjectStore".format(obj))
            # TODO only read files for non-skipped objects
            _collect_supplementary_files(reader, aas_part, part_objects, file_store)

            # Iterate split parts of AAS file
            for split_part in reader.get_related_parts_by_type(aas_part)[
                    "http://www.admin-shell.io/aasx/relationships/aas-spec-split"]:
                with reader.open_part(split_part) as aas_file:
                    part_objects = _parse_aas_part(aas_part, reader.get_content_type(aas_part), aas_file)
                for obj in part_objects:
                    if obj.identification in read_identifiables:
                        continue
                    if obj.identification not in object_store:
                        object_store.add(obj)
                        read_identifiables.add(obj.identification)
                    else:
                        logger.warning("Skipping {}, since an object with the same id is already contained in the "
                                       "ObjectStore".format(obj))
                # TODO only read files for non-skipped objects
                _collect_supplementary_files(reader, aas_part, part_objects, file_store)

    return read_identifiables


def _parse_aas_part(part_name: str, content_type: str, file_handle: IO) -> model.DictObjectStore:
    """
    TODO

    :param part_name:
    :param content_type:
    :param file_handle:
    :return:
    """
    extension = part_name.split("/")[-1].split(".")[-1]
    if content_type.split(";")[0] in ("text/xml", "application/xml") or content_type == "" and extension == "xml":
        # TODO XML Deserialization
        logger.debug("Parsing AAS objects from XML stream in OPC part {} ...".format(part_name))
        raise NotImplementedError("XML deserialization is not implemented yet. Thus, AASX files with XML parts are not "
                                  "supported.")
    elif content_type.split(";")[0] in ("text/json", "application/json") or content_type == "" and extension == "json":
        logger.debug("Parsing AAS objects from JSON stream in OPC part {} ...".format(part_name))
        return read_json_aas_file(file_handle)
    else:
        logger.error("Could not determine part format of AASX part {}".format(part_name))
        # TODO failsafe mode?
        raise ValueError("Unknown Content Type '{}' and extension '{}' of AASX part {}"
                         .format(content_type, extension, part_name))


def _collect_supplementary_files(reader: pyecma376_2.package_model.OPCPackageReader,
                                 part_name: str,
                                 objects: Iterable[model.Identifiable],
                                 file_store: "AbstractSupplementaryFileContainer") -> None:
    """
    TODO
    :param reader:
    :param part_name:
    :param objects:
    :param file_store:
    """
    for identifiable_object in objects:
        if isinstance(identifiable_object, model.Submodel):
            for element in traversal.walk_submodel(identifiable_object):
                if isinstance(element, model.File):
                    if element.value is None:
                        continue
                    absolute_name = pyecma376_2.package_model.part_realpath(element.value, part_name)
                    element.value = absolute_name
                    # TODO merge files by hash?
                    if absolute_name not in file_store:
                        logger.debug("Reading supplementary file {} from AASX package ...".format(absolute_name))
                        with reader.open_part(absolute_name) as p:
                            file_store.add_file(absolute_name, p, reader.get_content_type(absolute_name))


# TODO modify signature to take list of AAS ids and an AbstractObjectProvider to fetch the objects
# TODO allow to specify, which supplementary parts (submodels, conceptDescriptions) should be added to the package
# TODO allow to select JSON/XML serialization
def write_aasx(file: str,
               objects: model.AbstractObjectStore,
               files: "AbstractSupplementaryFileContainer",
               core_properties: pyecma376_2.OPCCoreProperties = pyecma376_2.OPCCoreProperties()) -> None:
    """
    TODO
    :param file:
    :param objects:
    :param files:
    :param core_properties:
    :return:
    """
    AASX_ORIGIN_PART_NAME = "/aasx/aasx-origin"

    # Create list of AAS ids to be added
    aas_to_add = [aas.identification for aas in objects if isinstance(aas, model.AssetAdministrationShell)]

    # Open OPC package file
    try:
        logger.debug("Creating AASX package in {} ...".format(file))
        writer = pyecma376_2.ZipPackageWriter(file)
    except Exception as e:
        raise ValueError("{} is not a valid ECMA376-2 (OPC) file".format(file)) from e

    with writer:
        # Create AASX origin part, CoreProperties part, and root relationships
        logger.debug("Creating AASX origin part in AASX package ...")
        p = writer.open_part(AASX_ORIGIN_PART_NAME, "text/plain")
        p.close()
        logger.debug("Writing core properties to AASX package ...")
        with writer.open_part(pyecma376_2.DEFAULT_CORE_PROPERTIES_NAME, "application/xml") as p:
            core_properties.write_xml(p)
        logger.debug("Writing package relationships to AASX package ...")
        writer.write_relationships((
            pyecma376_2.OPCRelationship("r1", "http://www.admin-shell.io/aasx/relationships/aasx-origin",
                                        AASX_ORIGIN_PART_NAME,
                                        pyecma376_2.OPCTargetMode.INTERNAL),
            pyecma376_2.OPCRelationship("r2", pyecma376_2.RELATIONSHIP_TYPE_CORE_PROPERTIES,
                                        pyecma376_2.DEFAULT_CORE_PROPERTIES_NAME,
                                        pyecma376_2.OPCTargetMode.INTERNAL)))

        # Create a part for each asset administration shell
        friendlyfier = NameFriendlyfier()
        aas_part_names: List[str] = []
        for aas_id in aas_to_add:
            aas_friendly_name = friendlyfier.get_friendly_name(aas_id)
            aas_part_name = "/aasx/{0}/{0}.aas.json".format(aas_friendly_name)
            aas_part_names.append(aas_part_name)
            aas_friendlyfier = NameFriendlyfier()

            aas: model.AssetAdministrationShell = objects.get_identifiable(aas_id)  # type: ignore
            objects_to_be_written: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
            objects_to_be_written.add(aas)

            # Add the Asset object to the objects in the AAS part
            try:
                objects_to_be_written.add(aas.asset.resolve(objects))
            except KeyError:
                # Don't add asset to the AASX file, if it is not included in the object store
                pass

            # Add referenced ConceptDescriptions to the AAS part
            for dictionary in aas.concept_dictionary:
                for concept_rescription_ref in dictionary.concept_description:
                    try:
                        objects_to_be_written.add(concept_rescription_ref.resolve(objects))
                    except KeyError:
                        # Don't add asset to the AASX file, if it is not included in the given object store
                        # Also ignore duplicate ConceptDescriptions (i.e. same Description referenced from multiple
                        # Dictionaries)
                        pass

            # Write AAS part
            logger.debug("Writing AAS {} to part {} in AASX package ...".format(aas.identification, aas_part_name))
            with writer.open_part(aas_part_name, "application/json") as p:
                write_aas_json_file(p, objects_to_be_written)

            # Create a AAS split part for each (available) submodel of the AAS
            submodel_part_names: List[str] = []
            for submodel_ref in aas.submodel:
                try:
                    submodel = submodel_ref.resolve(objects)
                except KeyError:
                    # Don't add submodel to the AASX file, if it is not included in the given object store
                    continue
                submodel_file_objects: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
                submodel_file_objects.add(submodel)
                submodel_friendly_name = aas_friendlyfier.get_friendly_name(submodel.identification)
                submodel_part_name = "/aasx/{0}/{1}/{1}.submodel.json".format(aas_friendly_name, submodel_friendly_name)
                submodel_part_names.append(submodel_part_name)
                logger.debug("Writing Submodel {} to part {} in AASX package ..."
                             .format(submodel.identification, submodel_part_name))
                with writer.open_part(submodel_part_name, "application/json") as p:
                    write_aas_json_file(p, submodel_file_objects)

                # Write submodel's supplementary files to AASX file
                submodel_file_names = []
                for element in traversal.walk_submodel(submodel):
                    if isinstance(element, model.File):
                        file_name = element.value
                        if file_name is None:
                            continue
                        try:
                            content_type = files.get_content_type(file_name)
                        except KeyError:
                            logger.warning("Could not find file {} in file store, referenced from {}."
                                           .format(file_name, element))
                            continue
                        # TODO avoid double writes of same file
                        logger.debug("Writing supplementary file {} to AASX package ...".format(file_name))
                        with writer.open_part(file_name, content_type) as p:
                            files.write_file(file_name, p)
                        submodel_file_names.append(pyecma376_2.package_model.normalize_part_name(file_name))

                # Add relationships from submodel to supplementary parts
                # TODO should the releationships be added from the AAS instead?
                logger.debug("Writing aas-suppl relationships for Submodel {} to AASX package ..."
                             .format(submodel.identification))
                writer.write_relationships(
                    (pyecma376_2.OPCRelationship("r{}".format(i),
                                                 "http://www.admin-shell.io/aasx/relationships/aas-suppl",
                                                 submodel_file_name,
                                                 pyecma376_2.OPCTargetMode.INTERNAL)
                     for i, submodel_file_name in enumerate(submodel_file_names)),
                    submodel_part_name)

            # Add relationships from AAS part to submodel parts
            logger.debug("Writing aasx-spec-split relationships for AAS {} to AASX package ..."
                         .format(aas.identification))
            writer.write_relationships(
                (pyecma376_2.OPCRelationship("r{}".format(i),
                                             "http://www.admin-shell.io/aasx/relationships/aasx-spec-split",
                                             submodel_part_name,
                                             pyecma376_2.OPCTargetMode.INTERNAL)
                 for i, submodel_part_name in enumerate(submodel_part_names)),
                aas_part_name)

        # Add relationships from AASX-origin part to AAS parts
        logger.debug("Writing aasx-spec relationships to AASX package ...")
        writer.write_relationships(
            (pyecma376_2.OPCRelationship("r{}".format(i), "http://www.admin-shell.io/aasx/relationships/aasx-spec",
                                         aas_part_name,
                                         pyecma376_2.OPCTargetMode.INTERNAL)
             for i, aas_part_name in enumerate(aas_part_names)),
            AASX_ORIGIN_PART_NAME)


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
    @abc.abstractmethod
    def add_file(self, name: str, file: IO[bytes], content_type: str) -> None:
        pass

    @abc.abstractmethod
    def get_content_type(self, name: str) -> str:
        pass

    @abc.abstractmethod
    def write_file(self, name: str, file: IO[bytes]) -> None:
        pass

    @abc.abstractmethod
    def __contains__(self, item: str) -> bool:
        pass


class DictSupplementaryFileContainer(AbstractSupplementaryFileContainer, Dict[str, Tuple[bytes, str]]):
    def add_file(self, name: str, file: IO[bytes], content_type: str) -> None:
        self[name] = (file.read(), content_type)

    def get_content_type(self, name: str) -> str:
        return self[name][1]

    def write_file(self, name: str, file: IO[bytes]) -> None:
        file.write(self[name][0])

    def __contains__(self, item: object) -> bool: ...   # This stub is required to make MyPy happy
