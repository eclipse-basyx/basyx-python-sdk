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
Helper classes for checking two objects for completeness and correctness and reporting the check results.
"""
import logging
import pprint
from typing import List, NamedTuple, Iterator, Dict, Any, Type, Union, Set, Iterable

from ... import model


class CheckResult(NamedTuple):
    expectation: str
    result: bool
    data: Dict[str, Any]

    def __repr__(self):
        return "{}: {} ({})".format("OK  " if self.result else "FAIL",
                                    self.expectation,
                                    ", ".join("{}={}".format(k, pprint.pformat(v, depth=2, width=2 ** 14, compact=True))
                                              for k, v in self.data.items()))


class DataChecker:
    """
    A helper class to perform multiple checks/assertions of given data and report the result.

    Typical usage:

        data = {'a': 1, 'b': 2}
        dc = DataChecker()
        dc.check(len(data) > 0, "data is not empty")
        if dc.check('a' in data, "a is in data", keys=list(data.keys())):
            dc.check(data['a'] == data['b'], "a == b", a=data['a'], b=data['b'])
            dc.check(data['a'] > 0, "a is positive", a=data['a'])

        for result in dc.failed_checks:
            print(result)
    """

    def __init__(self, raise_immediately: bool = False):
        """
        :param raise_immediately: If True, a failed check will raise an AssertionError instead of gathering the
                                  CheckResults for later analysis
        """
        self.checks: List[CheckResult] = []
        self.raise_immediately = raise_immediately

    def check(self, expression: bool, expectation: str, **kwargs) -> bool:
        """
        Checks if `expression` is True and adds / stores the check result for later analysis.

        :param expression: The boolean to be checked for
        :param expectation: A string describing, what the data was expected to look like (for later listing of
                            successful and failed checks)
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        if not expression and self.raise_immediately:
            raise AssertionError("Check failed: {}".format(expectation), kwargs)
        self.checks.append(CheckResult(expectation, expression, kwargs))
        return expression

    def extend(self, other: "DataChecker") -> None:
        """
        Extend the list of check results with another DataChecker's check results
        """
        self.checks.extend(other.checks)

    @property
    def failed_checks(self) -> Iterator[CheckResult]:
        return (result for result in self.checks if not result.result)

    @property
    def successful_checks(self) -> Iterator[CheckResult]:
        return (result for result in self.checks if result.result)

    def raise_failed(self) -> None:
        """
        Raise AssertionError if any check failed
        """
        failed = list(self.failed_checks)
        if len(failed) > 0:
            raise AssertionError("{} of {} checks failed".format(len(failed), len(self.checks)),
                                 [f.expectation for f in failed])


class AASDataChecker(DataChecker):
    def _check_submodel_element(self, object_: model.SubmodelElement, expected_object: model.SubmodelElement):
        if self.check_is_instance(object_, expected_object.__class__):
            if isinstance(object_, model.Property):
                return self.check_property_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.MultiLanguageProperty):
                return self.check_multi_language_property_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.Range):
                return self.check_range_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.Blob):
                return self.check_blob_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.File):
                return self.check_file_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.ReferenceElement):
                return self.check_reference_element_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.SubmodelElementCollection):
                return self.check_submodel_collection_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.AnnotatedRelationshipElement):
                return self.check_annotated_relationship_element_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.RelationshipElement):
                return self.check_relationship_element_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.Operation):
                return self.check_operation_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.Capability):
                return self.check_capability_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.Entity):
                return self.check_entity_equal(object_, expected_object)  # type: ignore
            if isinstance(object_, model.BasicEvent):
                return self.check_basic_event_equal(object_, expected_object)  # type: ignore
            else:
                raise AttributeError('Submodel Element class not implemented')

    def _check_referable_equal(self, object_: model.Referable, expected_object: model.Referable):
        """
        Checks if the referable object_ has the same referable attributes as the expected_value object and
        adds / stores the check result for later analysis.

        :param object_: The referable object which shall be checked
        :param expected_object: The expected referable object
        :return: The value of expression to be used in control statements
        """
        self.check_attribute_equal(object_, "id_short", expected_object.id_short)
        self.check_attribute_equal(object_, "category", expected_object.category)
        self.check_attribute_equal(object_, "description", expected_object.description)

    def _check_identifiable_equal(self, object_: model.Identifiable, expected_object: model.Identifiable):
        """
        Checks if the identifiable object_ has the same identifiable attributes as the expected_value object and
        adds / stores the check result for later analysis.

        :param object_: The identifiable object which shall be checked
        :param expected_object: The expected identifiable object
        :return: The value of expression to be used in control statements
        """
        self._check_referable_equal(object_, expected_object)
        self.check_attribute_equal(object_, "administration", expected_object.administration)
        self.check_attribute_equal(object_, "identification", expected_object.identification)

    def _check_has_semantics_equal(self, object_: model.HasSemantics, expected_object: model.HasSemantics):
        """
        Checks if the HasSemantic object_ has the same HasSemantics attributes as the expected_value object and
        adds / stores the check result for later analysis.

        :param object_: The HasSemantic object which shall be checked
        :param expected_object: The expected HasSemantic object
        :return: The value of expression to be used in control statements
        """
        self.check_attribute_equal(object_, "semantic_id", expected_object.semantic_id)

    def _check_has_kind_equal(self, object_: model.HasKind, expected_object: model.HasKind):
        """
        Checks if the HasKind object_ has the same HasKind attributes as the expected_value object and
        adds / stores the check result for later analysis.

        :param object_: The HasKind object which shall be checked
        :param expected_object: The expected HasKind object
        :return: The value of expression to be used in control statements
        """
        self.check_attribute_equal(object_, "kind", expected_object.kind)

    def _check_qualifiable_equal(self, object_: model.Qualifiable, expected_object: model.Qualifiable):
        """
        Checks if the qualifiable object_ has the same qualifiables attributes as the expected_value object and
        adds / stores the check result for later analysis.

        :param object_: The qualifiable object which shall be checked
        :param expected_object: The expected qualifiable object
        :return: The value of expression to be used in control statements
        """
        self.check_contained_element_length(object_, 'qualifier', model.Constraint, len(expected_object.qualifier))
        for expected_element in expected_object.qualifier:
            element = self._find_element_by_attribute(expected_element, list(object_.qualifier), 'type')
            if self.check(element is not None, 'Constraint {} must exist'.format(repr(expected_element))):
                if isinstance(element, model.Qualifier):
                    self._check_qualifier_equal(element, expected_element)  # type: ignore
                else:
                    raise TypeError('Constraint class not implemented')

        found_elements = self._find_extra_elements_by_attribute(list(object_.qualifier),
                                                                list(expected_object.qualifier), 'type')
        self.check(found_elements == set(), 'Qualifiable Element {} must not have extra elements'.format(repr(object_)),
                   value=found_elements)

    def _check_abstract_attributes_submodel_element_equal(self, object_: model.SubmodelElement,
                                                          expected_value: model.SubmodelElement):
        """
        Checks if the given SubmodelElement objects are equal

        :param object_: Given submodel element object to check
        :param expected_value: expected submodel element object
        :return:
        """
        self._check_referable_equal(object_, expected_value)
        self._check_has_semantics_equal(object_, expected_value)
        self._check_has_kind_equal(object_, expected_value)
        self._check_qualifiable_equal(object_, expected_value)

    def check_property_equal(self, object_: model.Property, expected_value: model.Property):
        """
        Checks if the given Property objects are equal

        :param object_: Given property object to check
        :param expected_value: expected property object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)
        self.check_attribute_equal(object_, 'value_type', expected_value.value_type)
        self.check_attribute_equal(object_, 'value', expected_value.value)
        self.check_attribute_equal(object_, 'value_id', expected_value.value_id)

    def check_multi_language_property_equal(self, object_: model.MultiLanguageProperty,
                                            expected_value: model.MultiLanguageProperty):
        """
        Checks if the given MultiLanguageProperty objects are equal

        :param object_: Given MultiLanguageProperty object to check
        :param expected_value: expected MultiLanguageProperty object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)
        self.check_attribute_equal(object_, 'value', expected_value.value)
        self.check_attribute_equal(object_, 'value_id', expected_value.value_id)

    def check_range_equal(self, object_: model.Range, expected_value: model.Range):
        """
        Checks if the given Range objects are equal

        :param object_: Given Range object to check
        :param expected_value: expected Range object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)
        self.check_attribute_equal(object_, 'value_type', expected_value.value_type)
        self.check_attribute_equal(object_, 'min', expected_value.min)
        self.check_attribute_equal(object_, 'max', expected_value.max)

    def check_blob_equal(self, object_: model.Blob, expected_value: model.Blob):
        """
        Checks if the given Blob objects are equal

        :param object_: Given Blob object to check
        :param expected_value: expected Blob object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)
        self.check_attribute_equal(object_, 'value', expected_value.value)
        self.check_attribute_equal(object_, 'mime_type', expected_value.mime_type)

    def check_file_equal(self, object_: model.File, expected_value: model.File):
        """
        Checks if the given File objects are equal

        :param object_: Given File object to check
        :param expected_value: expected File object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)
        self.check_attribute_equal(object_, 'value', expected_value.value)
        self.check_attribute_equal(object_, 'mime_type', expected_value.mime_type)

    def check_reference_element_equal(self, object_: model.ReferenceElement, expected_value: model.ReferenceElement):
        """
        Checks if the given ReferenceElement objects are equal

        :param object_: Given ReferenceElement object to check
        :param expected_value: expected ReferenceElement object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)
        self.check_attribute_equal(object_, 'value', expected_value.value)

    def check_submodel_collection_equal(self, object_: model.SubmodelElementCollection,
                                        expected_value: model.SubmodelElementCollection):
        """
        Checks if the given SubmodelElementCollection objects are equal

        :param object_: Given SubmodelElementCollection object to check
        :param expected_value: expected SubmodelElementCollection object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)
        if isinstance(object_, model.SubmodelElementCollectionUnordered) or \
                isinstance(object_, model.SubmodelElementCollectionUnorderedUniqueSemanticId):
            self._check_submodel_collection_unordered_equal(object_, expected_value)  # type: ignore
        elif isinstance(object_, model.SubmodelElementCollectionOrdered) or \
                isinstance(object_, model.SubmodelElementCollectionOrderedUniqueSemanticId):
            self._check_submodel_collection_ordered_equal(object_, expected_value)  # type: ignore
        else:
            raise AttributeError('Submodel Element collection class not implemented')

    def _check_submodel_collection_unordered_equal(self, object_: model.SubmodelElementCollectionUnordered,
                                                   expected_value: model.SubmodelElementCollectionUnordered):
        """
        Checks if the given SubmodelElementCollectionUnordered objects are equal

        :param object_: Given SubmodelElementCollectionUnordered object to check
        :param expected_value: expected SubmodelElementCollectionUnordered object
        :return:
        """
        self.check_contained_element_length(object_, 'value', model.SubmodelElement, len(expected_value.value))
        for expected_element in expected_value.value:
            if isinstance(expected_element, model.Referable):
                try:
                    element = object_.get_referable(expected_element.id_short)
                    self._check_submodel_element(element, expected_element)  # type: ignore
                except KeyError:
                    self.check(False, 'Submodel Element {} must exist'.format(repr(expected_element)))

        found_elements = self._find_extra_elements_by_id_short(object_.value, expected_value.value)
        self.check(found_elements == set(), 'Submodel Collection {} must not have extra elements'.format(repr(object_)),
                   value=found_elements)

    def _check_submodel_collection_ordered_equal(self, object_: model.SubmodelElementCollectionUnordered,
                                                 expected_value: model.SubmodelElementCollectionUnordered):
        """
        Checks if the given SubmodelElementCollectionUnordered objects are equal

        :param object_: Given SubmodelElementCollectionUnordered object to check
        :param expected_value: expected SubmodelElementCollectionUnordered object
        :return:
        """
        self.check_contained_element_length(object_, 'value', model.SubmodelElement, len(expected_value.value))
        list_values = list(object_.value)
        list_expected_values = list(expected_value.value)

        for i in range(len(list_expected_values)):
            self._check_submodel_element(list_values[i], list_expected_values[i])

    def check_relationship_element_equal(self, object_: model.RelationshipElement,
                                         expected_value: model.RelationshipElement):
        """
        Checks if the given RelationshipElement objects are equal

        :param object_: Given RelationshipElement object to check
        :param expected_value: expected RelationshipElement object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)
        self.check_attribute_equal(object_, 'first', expected_value.first)
        self.check_attribute_equal(object_, 'second', expected_value.second)

    def check_annotated_relationship_element_equal(self, object_: model.AnnotatedRelationshipElement,
                                                   expected_value: model.AnnotatedRelationshipElement):
        """
        Checks if the given AnnotatedRelationshipElement objects are equal

        :param object_: Given AnnotatedRelationshipElement object to check
        :param expected_value: expected AnnotatedRelationshipElement object
        :return:
        """
        self.check_relationship_element_equal(object_, expected_value)
        self.check_contained_element_length(object_, 'annotation', model.DataElement,
                                            len(expected_value.annotation))
        for expected_data_element in expected_value.annotation:
            try:
                object_.get_referable(expected_data_element.id_short)
            except KeyError:
                self.check(False, 'Annotation {} must exist'.format(repr(expected_data_element)))

        found_elements = self._find_extra_elements_by_id_short(object_.annotation, expected_value.annotation)
        self.check(found_elements == set(), 'Annotated Reference {} must not have extra '
                                            'references'.format(repr(object_)),
                   value=found_elements)

    def _check_reference_equal(self, object_: model.Reference, expected_value: model.Reference):
        """
        Checks if the given Reference objects are equal

        :param object_: Given Reference object to check
        :param expected_value: expected Reference object
        :return:
        """
        self.check(object_ == expected_value, "{} must be == {}".format(repr(object_), repr(expected_value)))

    def _find_reference(self, object_: model.Reference, search_list: Union[Set, List]) -> Union[model.Reference, None]:
        """
        Find a reference in an list

        :param object_: Given reference which should be find in list
        :param search_list: List in which the given reference should be find
        :return: the searched reference if found else none
        """
        for element in search_list:
            if object_ == element:
                return element
        return None

    def _find_identifier_key_value_pair(self, object_: model.IdentifierKeyValuePair, search_list: Union[Set, List]) \
            -> Union[model.IdentifierKeyValuePair, None]:
        """
        Find a IdentifierKeyValuePair in an list

        :param object_: Given IdentifierKeyValuePair which should be find in list
        :param search_list: List in which the given IdentifierKeyValuePair should be find
        :return: the searched IdentifierKeyValuePair if found else none
        """
        for element in search_list:
            if object_ == element:
                return element
        return None

    def _find_element_by_attribute(self, object_: object, search_list: Union[Set, List], *attribute: str) -> object:
        """
        Find an element in an list

        :param object_: Given object which should be find in list
        :param search_list: List in which the given object should be find
        :param attribute: List of attributes on which the comparison should be done
        :return:
        """
        find = False
        for element in search_list:
            if isinstance(element, object_.__class__):
                found = True
                for attr in attribute:
                    if getattr(object_, attr) != getattr(element, attr):
                        found = False
                if found:
                    return element
        return None

    def _find_extra_object(self, object_list: Iterable, search_list: Iterable,
                           type_) -> Union[Set, None]:
        """
        Find extra object that are in object_list but noch in search_list

        :param object_list: List which could contain more objects than the search_list has
        :param search_list: List which should be searched
        :param type_: type of objects which should be find
        :return: Set of objects that are in object_list but not in search_list
        """
        found_elements = set()
        for object_list_element in object_list:
            if isinstance(object_list_element, type_):
                found = False
                for search_list_element in search_list:
                    if isinstance(search_list_element, type_):
                        if object_list_element == search_list_element:
                            found = True
                            break
                if found is False:
                    found_elements.add(object_list_element)
        return found_elements

    def _find_extra_elements_by_attribute(self, object_list: Union[Set, List], search_list: Union[Set, List],
                                          *attribute: str) -> Set:
        """
        Find extra elements that are in object_list but not in search_list

        :param object_list: List which could contain more objects than the search_list has
        :param search_list: List which should be searched
        :param attribute: List of attributes on which the comparison should be done
        :return: Set of elements that are in object_list but not in search_list
        """
        found_elements = set()
        for object_list_element in object_list:
            found = False
            for search_list_element in search_list:
                for attr in attribute:
                    if getattr(object_list_element, attr) != getattr(search_list_element, attr):
                        found = False
                    else:
                        found = True
                if found:
                    break
            if found is False:
                found_elements.add(object_list_element)
        return found_elements

    def _find_extra_elements_by_id_short(self, object_list: model.NamespaceSet, search_list: model.NamespaceSet) -> Set:
        """
        Find extra elements that are in object_list but not in search_list

        :param object_list: List which could contain more objects than the search_list has
        :param search_list: List which should be searched
        :return: Set of elements that are in object_list but not in search_list
        """
        found_elements = set()
        for object_list_element in object_list:
            element = search_list.get("id_short", object_list_element.id_short)
            if element is None:
                found_elements.add(object_list_element)
        return found_elements

    def _check_operation_variable_equal(self, object_: model.OperationVariable,
                                        expected_value: model.OperationVariable):
        """
        Checks if the given OperationVariable objects are equal

        :param object_: Given OperationVariable object to check
        :param expected_value: expected OperationVariable object
        :return:
        """
        self._check_submodel_element(object_.value, expected_value.value)

    def check_operation_equal(self, object_: model.Operation, expected_value: model.Operation):
        """
        Checks if the given Operation objects are equal

        :param object_: Given Operation object to check
        :param expected_value: expected Operation object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)
        self.check_contained_element_length(object_, 'input_variable', model.OperationVariable,
                                            len(expected_value.input_variable))
        self.check_contained_element_length(object_, 'output_variable', model.OperationVariable,
                                            len(expected_value.output_variable))
        self.check_contained_element_length(object_, 'in_output_variable', model.OperationVariable,
                                            len(expected_value.in_output_variable))
        for i in range(len(object_.input_variable)):
            self._check_operation_variable_equal(object_.input_variable[i], expected_value.input_variable[i])
        for i in range(len(object_.output_variable)):
            self._check_operation_variable_equal(object_.output_variable[i], expected_value.output_variable[i])
        for i in range(len(object_.in_output_variable)):
            self._check_operation_variable_equal(object_.in_output_variable[i], expected_value.in_output_variable[i])

    def check_capability_equal(self, object_: model.Capability, expected_value: model.Capability):
        """
        Checks if the given Capability objects are equal

        :param object_: Given Capability object to check
        :param expected_value: expected Capability object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)

    def check_entity_equal(self, object_: model.Entity, expected_value: model.Entity):
        """
        Checks if the given Entity objects are equal

        :param object_: Given Entity object to check
        :param expected_value: expected Entity object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)
        self.check_attribute_equal(object_, 'entity_type', expected_value.entity_type)
        if object_.global_asset_id and expected_value.global_asset_id:
            self._check_reference_equal(object_.global_asset_id, expected_value.global_asset_id)
        else:
            if expected_value.global_asset_id:
                self.check(expected_value.global_asset_id is not None,
                           'globalAssetId {} must exist'.format(repr(expected_value.global_asset_id)),
                           value=object_.global_asset_id)
            else:
                if object_.global_asset_id:
                    self.check(expected_value.global_asset_id is None, 'Enity {} must not have a '
                                                                       'globalAssetId'.format(repr(object_)),
                               value=expected_value.global_asset_id)
        if object_.specific_asset_id and expected_value.specific_asset_id:
            self.check_identifier_key_value_pair(object_.specific_asset_id, expected_value.specific_asset_id)
        else:
            if expected_value.specific_asset_id:
                self.check(expected_value.specific_asset_id is not None,
                           'SpecificAssetId {} must exist'.format(repr(expected_value.specific_asset_id)),
                           value=object_.specific_asset_id)
            else:
                if object_.specific_asset_id:
                    self.check(expected_value.specific_asset_id is None, 'Enity {} must not have a '
                                                                         'specificAssetId'.format(repr(object_)),
                               value=expected_value.specific_asset_id)
        self.check_contained_element_length(object_, 'statement', model.SubmodelElement, len(expected_value.statement))
        for expected_element in expected_value.statement:
            element = object_.get_referable(expected_element.id_short)
            self.check(element is not None, 'Entity {} must exist'.format(repr(expected_element)))

        found_elements = self._find_extra_elements_by_id_short(object_.statement, expected_value.statement)
        self.check(found_elements == set(), 'Enity {} must not have extra statements'.format(repr(object_)),
                   value=found_elements)

    def _check_event_equal(self, object_: model.Event, expected_value: model.Event):
        """
        Checks if the given Event objects are equal

        :param object_: Given Event object to check
        :param expected_value: expected Event object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)

    def check_basic_event_equal(self, object_: model.BasicEvent, expected_value: model.BasicEvent):
        """
        Checks if the given BasicEvent objects are equal

        :param object_: Given BasicEvent object to check
        :param expected_value: expected BasicEvent object
        :return:
        """
        self._check_abstract_attributes_submodel_element_equal(object_, expected_value)
        self._check_event_equal(object_, expected_value)
        self.check_attribute_equal(object_, 'observed', expected_value.observed)

    def check_submodel_equal(self, object_: model.Submodel, expected_value: model.Submodel):
        """
        Checks if the given Submodel objects are equal

        :param object_: Given Submodel object to check
        :param expected_value: expected Submodel object
        :return:
        """
        self._check_identifiable_equal(object_, expected_value)
        self._check_has_semantics_equal(object_, expected_value)
        self._check_has_kind_equal(object_, expected_value)
        self._check_qualifiable_equal(object_, expected_value)
        self.check_contained_element_length(object_, 'submodel_element', model.SubmodelElement,
                                            len(expected_value.submodel_element))
        for expected_element in expected_value.submodel_element:
            try:
                element = object_.get_referable(expected_element.id_short)
                self._check_submodel_element(element, expected_element)  # type: ignore
            except KeyError:
                self.check(False, 'Submodel Element {} must exist'.format(repr(expected_element)))

        found_elements = self._find_extra_elements_by_id_short(object_.submodel_element,
                                                               expected_value.submodel_element)
        self.check(found_elements == set(), 'Submodel {} must not have extra submodel elements'.format(repr(object_)),
                   value=found_elements)

    def _check_qualifier_equal(self, object_: model.Qualifier, expected_value: model.Qualifier):
        """
        Checks if the given Qualifier objects are equal

        :param object_: Given Qualifier object to check
        :param expected_value: expected Qualifier object
        :return:
        """
        self.check_attribute_equal(object_, 'type', expected_value.type)
        self.check_attribute_equal(object_, 'value_type', expected_value.value_type)
        self.check_attribute_equal(object_, 'value', expected_value.value)
        self.check_attribute_equal(object_, 'value_id', expected_value.value_id)

    def check_identifier_key_value_pair(self, object_: model.IdentifierKeyValuePair,
                                        expected_value: model.IdentifierKeyValuePair):
        """
        Checks if the given IdentifierKeyValuePair objects are equal

        :param object_: Given IdentifierKeyValuePair object to check
        :param expected_value: expected IdentifierKeyValuePair object
        :return:
        """
        self.check_attribute_equal(object_, "key", expected_value.key)
        self.check_attribute_equal(object_, "value", expected_value.value)
        self.check_attribute_equal(object_, "external_subject_id", expected_value.external_subject_id)

    def check_asset_information_equal(self, object_: model.AssetInformation, expected_value: model.AssetInformation):
        """
        Checks if the given AssetInformation objects are equal

        :param object_: Given AssetInformation object to check
        :param expected_value: expected AssetInformation object
        :return:
        """
        self.check_attribute_equal(object_, 'asset_kind', expected_value.asset_kind)
        self._check_reference_equal(object_.global_asset_id, expected_value.global_asset_id)
        self.check_contained_element_length(object_, 'specific_asset_id', model.IdentifierKeyValuePair,
                                            len(expected_value.specific_asset_id))
        for expected_pair in expected_value.specific_asset_id:
            pair = self._find_identifier_key_value_pair(expected_pair, object_.specific_asset_id)
            if self.check(pair is not None, 'IdentifierValueKeyPair {} must exist'.format(repr(expected_pair))):
                self.check_identifier_key_value_pair(pair, expected_pair)  # type: ignore

        found_elements = self._find_extra_object(object_.specific_asset_id, expected_value.specific_asset_id,
                                                 model.IdentifierKeyValuePair)
        self.check(found_elements == set(), 'AssetInformation {} must not have extra '
                                            'specificAssetIds'.format(repr(object_)),
                   value=found_elements)

        self.check_contained_element_length(object_, 'bill_of_material', model.AASReference,
                                            len(expected_value.bill_of_material))
        for expected_ref in expected_value.bill_of_material:
            ref = self._find_reference(expected_ref, object_.bill_of_material)
            if self.check(ref is not None, 'AAS Reference {} must exist'.format(repr(expected_ref))):
                self._check_reference_equal(ref, expected_ref)  # type: ignore

        found_elements = self._find_extra_object(object_.bill_of_material, expected_value.bill_of_material,
                                                 model.AASReference)
        self.check(found_elements == set(), 'AssetInformation {} must not have extra '
                                            'references'.format(repr(object_)),
                   value=found_elements)

        if object_.default_thumbnail and expected_value.default_thumbnail:
            self.check_file_equal(object_.default_thumbnail, expected_value.default_thumbnail)
        else:
            if object_.default_thumbnail:
                self.check(expected_value.default_thumbnail is not None,
                           'Thumbnail object {} must exist'.format(repr(object_.default_thumbnail)),
                           value=expected_value.default_thumbnail)
            else:
                self.check(expected_value.default_thumbnail is None, 'Asset Administration Shell {} must not have a '
                                                                     'Thumbnail object'.format(repr(object_)),
                           value=expected_value.default_thumbnail)

    def check_asset_administration_shell_equal(self, object_: model.AssetAdministrationShell,
                                               expected_value: model.AssetAdministrationShell):
        """
        Checks if the given AssetAdministrationShell objects are equal

        :param object_: Given AssetAdministrationShell object to check
        :param expected_value: expected AssetAdministrationShell object
        :return:
        """
        self._check_identifiable_equal(object_, expected_value)
        self.check_asset_information_equal(object_.asset_information, expected_value.asset_information)
        if object_.security and expected_value.security:
            self.check_security_equal(object_.security, expected_value.security)
        else:
            if expected_value.security:
                self.check(expected_value.security is not None,
                           'Security object {} must exist'.format(repr(expected_value.security)),
                           value=object_.security)
            else:
                self.check(expected_value.security is None, 'Asset Administration Shell {} must not have a security '
                                                            'object'.format(repr(expected_value)),
                           value=object_.security)

        self.check_attribute_equal(object_, 'derived_from', expected_value.derived_from)
        self.check_contained_element_length(object_, 'submodel', model.AASReference, len(expected_value.submodel))
        self.check_contained_element_length(object_, 'view', model.View, len(expected_value.view))
        for expected_ref in expected_value.submodel:
            ref = self._find_reference(expected_ref, object_.submodel)
            if self.check(ref is not None, 'Submodel Reference {} must exist'.format(repr(expected_ref))):
                self._check_reference_equal(ref, expected_ref)  # type: ignore

        found_elements = self._find_extra_object(object_.submodel, expected_value.submodel, model.AASReference)
        self.check(found_elements == set(), 'Asset Administration Shell {} must not have extra submodel '
                                            'references'.format(repr(object_)),
                   value=found_elements)

        for expected_view in expected_value.view:
            try:
                view = object_.get_referable(expected_view.id_short)
                self.check_view_equal(view, expected_view)  # type: ignore
            except KeyError:
                self.check(False, 'View {} must exist'.format(repr(expected_view)))

        found_elements = self._find_extra_elements_by_id_short(object_.view, expected_value.view)
        self.check(found_elements == set(), 'Asset Administration Shell {} must not have extra '
                                            'views'.format(repr(object_)), value=found_elements)

    def check_security_equal(self, object_: model.Security,
                             expected_value: model.Security):
        """
        Checks if the given Security objects are equal

        :param object_: Given Security object to check
        :param expected_value: expected Security object
        :return:
        """
        # TODO: if security is specified
        pass

    def check_view_equal(self, object_: model.View, expected_value: model.View):
        """
        Checks if the given View objects are equal

        :param object_: Given View object to check
        :param expected_value: expected View object
        :return:
        """
        self._check_referable_equal(object_, expected_value)
        self._check_has_semantics_equal(object_, expected_value)
        self.check_contained_element_length(object_, 'contained_element', model.AASReference,
                                            len(expected_value.contained_element))

        for expected_ref in expected_value.contained_element:
            ref = self._find_reference(expected_ref, object_.contained_element)
            if self.check(ref is not None, 'View Reference {} must exist'.format(repr(expected_ref))):
                self._check_reference_equal(ref, expected_ref)  # type: ignore

        found_elements = self._find_extra_object(object_.contained_element, expected_value.contained_element,
                                                 model.AASReference)
        self.check(found_elements == set(), 'View Reference {} must not have extra '
                                            'submodel element references'.format(repr(object_)),
                   value=found_elements)

    def check_concept_description_equal(self, object_: model.ConceptDescription,
                                        expected_value: model.ConceptDescription):
        """
        Checks if the given ConceptDescription objects are equal

        :param object_: Given ConceptDescription object to check
        :param expected_value: expected ConceptDescription object
        :return:
        """
        self._check_identifiable_equal(object_, expected_value)
        self.check_contained_element_length(object_, 'is_case_of', model.Reference,
                                            len(expected_value.is_case_of))
        for expected_ref in expected_value.is_case_of:
            ref = self._find_reference(expected_ref, object_.is_case_of)
            if self.check(ref is not None, 'Concept Description Reference {} must exist'.format(repr(expected_ref))):
                self._check_reference_equal(ref, expected_ref)  # type: ignore

        found_elements = self._find_extra_object(object_.is_case_of, expected_value.is_case_of,
                                                 model.AASReference)
        self.check(found_elements == set(), 'Concept Description Reference {} must not have extra '
                                            'is case of references'.format(repr(object_)),
                   value=found_elements)

        if isinstance(expected_value, model.IEC61360ConceptDescription):
            if self.check_is_instance(object_, model.IEC61360ConceptDescription):
                self._check_iec61360_concept_description_equal(object_, expected_value)  # type: ignore

    def _check_iec61360_concept_description_equal(self, object_: model.IEC61360ConceptDescription,
                                                  expected_value: model.IEC61360ConceptDescription):
        """
        Checks if the given IEC61360ConceptDescription objects are equal

        :param object_: Given IEC61360ConceptDescription object to check
        :param expected_value: expected IEC61360ConceptDescription object
        :return:
        """
        self.check_attribute_equal(object_, 'preferred_name', expected_value.preferred_name)
        self.check_attribute_equal(object_, 'short_name', expected_value.short_name)
        self.check_attribute_equal(object_, 'data_type', expected_value.data_type)
        self.check_attribute_equal(object_, 'definition', expected_value.definition)
        self.check_attribute_equal(object_, 'unit', expected_value.unit)
        self.check_attribute_equal(object_, 'unit_id', expected_value.unit_id)
        self.check_attribute_equal(object_, 'source_of_definition', expected_value.source_of_definition)
        self.check_attribute_equal(object_, 'symbol', expected_value.symbol)
        self.check_attribute_equal(object_, 'value_format', expected_value.value_format)
        self.check_attribute_equal(object_, 'value', expected_value.value)
        self.check_attribute_equal(object_, 'value_id', expected_value.value_id)
        self.check_attribute_equal(object_, 'level_types', expected_value.level_types)

        if expected_value.value_list is not None:
            if self.check(object_.value_list is not None,
                          "ValueList must contain {} ValueReferencePairs".format(len(expected_value.value_list)),
                          value=expected_value.value_list):
                self._check_value_list_equal(object_.value_list, expected_value.value_list)  # type: ignore

        if object_.value_list is not None:
            if self.check(expected_value.value_list is not None,
                          "ValueList must contain 0 ValueReferencePairs", value=len(object_.value_list)):
                self._check_value_list_equal(object_.value_list, expected_value.value_list)  # type: ignore

    def _check_value_list_equal(self, object_: model.ValueList, expected_value: model.ValueList):
        """
        Checks if the given ValueList objects are equal

        :param object_: Given ValueList object to check
        :param expected_value: expected ValueList object
        :return:
        """
        for expected_pair in expected_value:
            pair = self._find_element_by_attribute(expected_pair, object_, 'value', 'value_id', 'value_type')
            self.check(pair is not None, 'ValueReferencePair[value={}, value_id={}, value_type={}] '
                                         'must exist'.format(expected_pair.value, expected_pair.value_id,
                                                             expected_pair.value_type))

        found_elements = self._find_extra_elements_by_attribute(object_, expected_value,
                                                                'value', 'value_id', 'value_type')
        self.check(found_elements == set(), 'ValueReferenceList must not have extra ValueReferencePairs',
                   value=found_elements)

    def check_object_store(self, obj_store_1: model.DictObjectStore, obj_store_2: model.DictObjectStore):
        """
        Checks if the given object stores are equal

        :param obj_store_1: Given object store to check
        :param obj_store_2: expected object store
        :return:
        """
        # separate different kind of objects
        asset_list_1 = []
        submodel_list_1 = []
        concept_description_list_1 = []
        shell_list_1 = []
        for obj in obj_store_1:
            if isinstance(obj, model.Asset):
                asset_list_1.append(obj)
            elif isinstance(obj, model.AssetAdministrationShell):
                shell_list_1.append(obj)
            elif isinstance(obj, model.Submodel):
                submodel_list_1.append(obj)
            elif isinstance(obj, model.ConceptDescription):
                concept_description_list_1.append(obj)
            else:
                raise KeyError('Check for {} not implemented'.format(obj))

        # separate different kind of objects
        asset_list_2 = []
        submodel_list_2 = []
        concept_description_list_2 = []
        shell_list_2 = []
        for obj in obj_store_2:
            if isinstance(obj, model.Asset):
                asset_list_2.append(obj)
            elif isinstance(obj, model.AssetAdministrationShell):
                shell_list_2.append(obj)
            elif isinstance(obj, model.Submodel):
                submodel_list_2.append(obj)
            elif isinstance(obj, model.ConceptDescription):
                concept_description_list_2.append(obj)
            else:
                raise KeyError('Check for {} not implemented'.format(obj))

        for asset_2 in asset_list_2:
            asset_1 = obj_store_1.get(asset_2.identification)
            if self.check(asset_1 is not None, 'Asset {} must exist in given asset list'.format(asset_2)):
                self.check_asset_equal(asset_1, asset_2)  # type: ignore

        found_elements = self._find_extra_elements_by_attribute(asset_list_1, asset_list_2, 'identification')
        self.check(found_elements == set(), 'Given asset list must not have extra assets',
                   value=found_elements)

        for shell_2 in shell_list_2:
            shell_1 = obj_store_1.get(shell_2.identification)
            if self.check(shell_1 is not None, 'Asset administration shell {} must exist in given asset administration'
                                               'shell list'.format(shell_2)):
                self.check_asset_administration_shell_equal(shell_1, shell_2)  # type: ignore

        found_elements = self._find_extra_elements_by_attribute(shell_list_1, shell_list_2, 'identification')
        self.check(found_elements == set(), 'Given asset administration shell list must not have extra asset '
                                            'administration shells', value=found_elements)

        for submodel_2 in submodel_list_2:
            submodel_1 = obj_store_1.get(submodel_2.identification)
            if self.check(submodel_1 is not None, 'Submodel {} must exist in given submodel list'.format(submodel_2)):
                self.check_submodel_equal(submodel_1, submodel_2)  # type: ignore

        found_elements = self._find_extra_elements_by_attribute(submodel_list_1, submodel_list_2, 'identification')
        self.check(found_elements == set(), 'Given submodel list must not have extra submodels',
                   value=found_elements)

        for cd_2 in concept_description_list_2:
            cd_1 = obj_store_1.get(cd_2.identification)
            if self.check(cd_1 is not None, 'Concept description {} must exist in given concept description '
                                            'list'.format(cd_2)):
                self.check_concept_description_equal(cd_1, cd_2)  # type: ignore

        found_elements = self._find_extra_elements_by_attribute(concept_description_list_1, concept_description_list_2,
                                                                'identification')
        self.check(found_elements == set(), 'Given concept description list must not have extra concept '
                                            'descriptions',
                   value=found_elements)

    def check_attribute_equal(self, object_: object, attribute_name: str, expected_value: object, **kwargs) -> bool:
        """
        Checks if the value of the attribute in object_ is the same as expected_value and adds / stores the
        check result for later analysis.

        :param object_: The object of which the attribute shall be checked
        :param attribute_name: The name of the attribute in the given object which shall be checked
        :param expected_value: The expected value of the attribute
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        if attribute_name == 'value_type':
            kwargs['value'] = getattr(object_, attribute_name).__name__
            return self.check(getattr(object_, attribute_name) is expected_value,  # type:ignore
                              "Attribute {} of {} must be == {}".format(
                                  attribute_name, repr(object_), expected_value.__name__),  # type:ignore
                              **kwargs)
        else:
            kwargs['value'] = getattr(object_, attribute_name)
            return self.check(getattr(object_, attribute_name) == expected_value,
                              "Attribute {} of {} must be == {}".format(attribute_name, repr(object_), expected_value),
                              **kwargs)

    def check_element_in(self, object_: model.Referable, parent: object, **kwargs) -> bool:
        """
        Checks if object_ exist in parent and adds / stores the check result for later analysis.

        :param object_: The object which shall be in parent
        :param parent: The parent in which object_ shall be exist
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        Existence check: <path to object> must exist in <object class> (<path to object>)
        """
        return self.check(object_.parent == parent,
                          "{} must exist in {}s".format(repr(object_), repr(parent)),
                          **kwargs)

    def check_contained_element_length(self, object_: object, attribute_name: str, class_name: Type,
                                       length: int, **kwargs) -> bool:
        """
        Checks if the object_ has <lenght> elements of class <class_name> in attribute <attribute_name> and
        adds / stores the check result for later analysis.

        :param object_: The object of which the attribute shall be checked
        :param attribute_name: The name of the attribute in the given object which shall be checked
        :param class_name: The class name to decide which objects in the attribute shall be count
        :param length: The expected length of the attribute
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        count = 0
        for element in getattr(object_, attribute_name):
            if isinstance(element, class_name):
                count = count + 1
        kwargs['count'] = count
        return self.check(count == length,
                          "Attribute {} of {} must contain {} {}s".format(attribute_name, repr(object_),
                                                                          length, class_name.__name__),
                          **kwargs)

    def check_is_instance(self, object_: object, class_name: Type, **kwargs) -> bool:
        """
        Checks if the value of the attribute in object_ is None and adds / stores the check result for later analysis.

        :param object_: The object of which the attribute shall be checked
        :param class_name: The class name which the object_ shall be
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        kwargs['class'] = object_.__class__.__name__
        return self.check(isinstance(object_, class_name),
                          "{} must be of class {}".format(repr(object_), class_name.__name__),
                          **kwargs)

    def check_attribute_is_none(self, object_: object, attribute_name: str, **kwargs) -> bool:
        """
        Checks if the value of the attribute in object_ is None and adds / stores the check result for later analysis.

        :param object_: The object of which the attribute shall be checked
        :param attribute_name: The name of the attribute in the given object which shall be checked
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        kwargs['value'] = getattr(object_, attribute_name)
        return self.check(getattr(object_, attribute_name) is None,
                          "Attribute {} of {} must be None".format(attribute_name, repr(object_)),
                          **kwargs)
