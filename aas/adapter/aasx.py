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
import os
import re
import io
from typing import Dict, Tuple, IO, Union, List, Set, Optional, Callable

from .. import model
from .json.json_deserialization import read_json_aas_file
from .json.json_serialization import write_aas_json_file
import pyecma376_2


# TODO allow relative referencing of returned supplementary files
# TODO allow reading thumbnail image
def read_aasx(file: Union[os.PathLike, str, IO]) -> Tuple[model.AbstractObjectStore,
                                                          Dict[str, bytes],
                                                          pyecma376_2.OPCCoreProperties]:
    """
    TODO
    :param file:
    :return:
    """
    # Open file as OPC package file
    try:
        reader = pyecma376_2.ZipPackageReader(file)
    except Exception as e:
        raise ValueError("{} is not a valid ECMA376-2 (OPC) file".format(file)) from e

    with reader:
        # Find AASX-Origin part
        core_rels = reader.get_related_parts_by_type()
        try:
            aasx_origin_part = core_rels["http://www.admin-shell.io/aasx/relationships/aasx-origin"][0]
        except IndexError as e:
            raise ValueError("{} is not a valid AASX file: aasx-origin Relationship is missing.".format(file)) \
                from e

        result_objects: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        supplementary_files: Dict[str, bytes] = {}

        # Iterate AAS files
        for aas_part in reader.get_related_parts_by_type(aasx_origin_part)[
                "http://www.admin-shell.io/aasx/relationships/aas-spec"]:
            with reader.open_part(aas_part) as aas_file:
                # TODO ignore KeyError which may occur due to redundant storage in different file formats
                result_objects.update(_parse_aas_part(aas_part, reader.get_content_type(aas_part), aas_file))

            # Iterate split parts of AAS file
            for split_part in reader.get_related_parts_by_type(aas_part).get(
                    "http://www.admin-shell.io/aasx/relationships/aas-spec-split", []):
                with reader.open_part(split_part) as aas_file:
                    # TODO ignore KeyError which may occur due to redundant storage in different file formats
                    result_objects.update(_parse_aas_part(aas_part, reader.get_content_type(aas_part), aas_file))
                # TODO load supplementary files here, too?

            # Load supplementary files referenced by AAS file
            for suppl_part in reader.get_related_parts_by_type(aas_part).get(
                    "http://www.admin-shell.io/aasx/relationships/aas-suppl", []):
                with reader.open_part(suppl_part) as suppl_file:
                    supplementary_files[suppl_part] = suppl_file.read()

        return result_objects, supplementary_files, reader.get_core_properties()


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
        return model.DictObjectStore()
    elif content_type.split(";")[0] in ("text/json", "application/json") or content_type == "" and extension == "json":
        return read_json_aas_file(file_handle)
    else:
        raise ValueError("Unknown Content Type '{}' and extension '{}' of part {}"
                         .format(content_type, extension, part_name))


# TODO extend signature to allow writing supplementary files
# TODO modify signature to take list of AAS ids and an AbstractObjectProvider to fetch the objects
# TODO allow to specify, which supplementary parts (submodels, conceptDescriptions) should be added to the package
# TODO allow to select JSON/XML serialization
def write_aasx(file: str,
               objects: model.AbstractObjectStore,
               core_properties: pyecma376_2.OPCCoreProperties = pyecma376_2.OPCCoreProperties()) -> None:
    """
    TODO
    :param file:
    :param objects:
    :param core_properties:
    :return:
    """
    AASX_ORIGIN_PART_NAME = "/aasx/aasx-origin"

    # Create list of AAS ids to be added
    aas_to_add = [aas.identification for aas in objects if isinstance(aas, model.AssetAdministrationShell)]

    # Open OPC package file
    try:
        writer = pyecma376_2.ZipPackageWriter(file)
    except Exception as e:
        raise ValueError("{} is not a valid ECMA376-2 (OPC) file".format(file)) from e

    with writer:
        # Create AASX origin part, CoreProperties part, and root relationships
        p = writer.open_part(AASX_ORIGIN_PART_NAME, "text/plain")
        p.close()
        with writer.open_part(pyecma376_2.DEFAULT_CORE_PROPERTIES_NAME, "application/xml") as p:
            core_properties.write_xml(p)
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
                submodel_file_objects = model.DictObjectStore()
                submodel_file_objects.add(submodel)
                submodel_friendly_name = aas_friendlyfier.get_friendly_name(submodel.identification)
                submodel_part_name = "/aasx/{0}/{1}/{1}.submodel.json".format(aas_friendly_name, submodel_friendly_name)
                submodel_part_names.append(submodel_part_name)
                with writer.open_part(submodel_part_name, "application/json") as p:
                    write_aas_json_file(p, submodel_file_objects)

            # TODO Write supplementary files of AAS (and submodels?)

            # Add relationships from AAS part to submodel parts
            writer.write_relationships(
                (pyecma376_2.OPCRelationship("r1", "http://www.admin-shell.io/aasx/relationships/aasx-spec-split",
                                                submodel_part_name,
                                                pyecma376_2.OPCTargetMode.INTERNAL)
                 for submodel_part_name in submodel_part_names),
                aas_part_name)

        # Add relationships from AASX-origin part to AAS parts
        writer.write_relationships(
            (pyecma376_2.OPCRelationship("r1", "http://www.admin-shell.io/aasx/relationships/aasx-spec",
                                         aas_part_name,
                                         pyecma376_2.OPCTargetMode.INTERNAL)
             for aas_part_name in aas_part_names),
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


class SupplementaryFileContainer:
    def __init__(self):
        # Each entry is: (absolute path within AASX,
        #                 {context identifier: relative path from context},
        #                 content type,
        #                 payload)
        self._data: List[Tuple[Optional[str], Dict[model.Identifier, str], str, bytes]] = []

    def add(self, context_identifier: model.Identifier, path: str, payload: bytes, content_type: str = "") -> None:
        # TODO if absolute path:
        # TODO check if already existing with absolute path: Then add reference from this
        pass

    def get(self, context_identifier: model.Identifier, path: str) -> Tuple[bytes, str]:
        if path[0] == "/":
            for abs_part, _refs, content_type, payload in self._data:
                if (pyecma376_2.package_model.normalize_part_name(path)
                        == pyecma376_2.package_model.normalize_part_name(abs_part)):
                    return payload, content_type
            raise KeyError()
        else:
            for _abs_part, refs, content_type, payload in self._data:
                if (pyecma376_2.package_model.normalize_part_name(path)
                        == pyecma376_2.package_model.normalize_part_name(refs.get(context_identifier, ''))):
                    return payload, content_type
            raise KeyError()

    def read_from_aas(self, part_name: str,
                      context_identifier: model.Identifier,
                      part_content: io.BytesIO,
                      content_type: str) -> None:
        for abs_part, refs, _type, _payload in self._data:
            if part_name == abs_part:
                refs[context_identifier] = ""  # TODO relative path
            return
        self._data.append((part_name, {context_identifier: ""}, content_type, part_content.read()))  # TODO

    def write_relative_of_context(self, context_identifier: model.Identifier,
                                   writer_factory: Callable[[str, str], io.BytesIO]) -> None:



