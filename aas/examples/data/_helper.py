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
Helper classes for checking example data structures for completeness and correctness and reporting the check results.
"""

import pprint
from typing import List, NamedTuple, Iterator, Dict, Any, Type, Optional

from aas import model
from aas.model import LangStringSet, Namespace


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
    def _check_submodel_element(self, object_: model.SubmodelElement, expected_object: model.SubmodelElement) -> bool:
        self.check_is_instance(object_, expected_object.__class__)
        if isinstance(object_, model.Property):
            return self._check_property_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.MultiLanguageProperty):
            return self._check_multi_language_property_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.Range):
            return self._check_range_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.Blob):
            return self._check_blob_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.File):
            return self._check_file_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.ReferenceElement):
            return self._check_reference_element_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.SubmodelElementCollection):
            return self._check_submodel_collection_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.AnnotatedRelationshipElement):
            return self._check_annotated_relationship_element_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.RelationshipElement):
            return self._check_relationship_element_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.Operation):
            return self._check_operation_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.Capability):
            return self._check_capability_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.Entity):
            return self._check_entity_equal(object_, expected_object)  # type: ignore
        if isinstance(object_, model.BasicEvent):
            return self._check_basic_event_equal(object_, expected_object)  # type: ignore
        return False

    def _check_referable_equal(self, object_: model.Referable, expected_object: model.Referable) -> bool:
        """
        Checks if the referable object_ has the same referable attributes as the expected_value object and
        adds / stores the check result for later analysis.

        :param object_: The referable object which shall be checked
        :param expected_object: The expected referable object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        return (self.check_attribute_equal(object_, "id_short", expected_object.id_short) and
                self.check_attribute_equal(object_, "category", expected_object.category) and
                self.check_attribute_equal(object_, "description", expected_object.description))

    def _check_identifiable_equal(self, object_: model.Identifiable, expected_object: model.Identifiable) -> bool:
        """
        Checks if the identifiable object_ has the same identifiable attributes as the expected_value object and
        adds / stores the check result for later analysis.

        :param object_: The identifiable object which shall be checked
        :param expected_object: The expected identifiable object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        return (self._check_referable_equal(object_, expected_object) and
                self.check_attribute_equal(object_, "administration", expected_object.administration) and
                self.check_attribute_equal(object_, "identification", expected_object.identification))

    def _check_has_semantics_equal(self, object_: model.HasSemantics, expected_object: model.HasSemantics) -> bool:
        """
        Checks if the HasSemantic object_ has the same HasSemantics attributes as the expected_value object and
        adds / stores the check result for later analysis.

        :param object_: The HasSemantic object which shall be checked
        :param expected_object: The expected HasSemantic object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        return self.check_attribute_equal(object_, "semantic_id", expected_object.semantic_id)

    def _check_has_kind_equal(self, object_: model.HasKind, expected_object: model.HasKind) -> bool:
        """
        Checks if the HasKind object_ has the same HasKind attributes as the expected_value object and
        adds / stores the check result for later analysis.

        :param object_: The HasKind object which shall be checked
        :param expected_object: The expected HasKind object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        return self.check_attribute_equal(object_, "kind", expected_object.kind)

    def _check_qualifiable_equal(self, object_: model.Qualifiable, expected_object: model.Qualifiable) -> bool:
        """
        Checks if the qualifiable object_ has the same qualifiables attributes as the expected_value object and
        adds / stores the check result for later analysis.

        :param object_: The qualifiable object which shall be checked
        :param expected_object: The expected qualifiable object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return: The value of expression to be used in control statements
        """
        # TODO add check of formula => not clear how to identify a formula
        result = self.check_contained_element_length(object_, 'qualifier', model.Constraint,
                                                     len(expected_object.qualifier))
        for constraint in object_.qualifier:
            if isinstance(constraint, model.Qualifier):
                find = False
                for expected_constraint in expected_object.qualifier:
                    if isinstance(expected_constraint, model.Qualifier):
                        if constraint.type_ == expected_constraint.type_:
                            result = result and self._check_qualifier_equal(constraint, expected_constraint)
                            find = True
                            break
                if not find:
                    result = result and self.check(False, 'Qualifier[{}] not found'.format(constraint.type_))
        return result

    def _check_abstract_attributes_submodel_element_equal(self, object_: model.SubmodelElement,
                                                          expected_value: model.SubmodelElement):
        """
        Checks if the given SubmodelElement objects are equal

        :param object_: Given submodel element object to check
        :param expected_value: expected submodel element object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self._check_referable_equal(object_, expected_value) and
                self._check_has_semantics_equal(object_, expected_value) and
                self._check_has_kind_equal(object_, expected_value) and
                self._check_qualifiable_equal(object_, expected_value))

    def _check_property_equal(self, object_: model.Property, expected_value: model.Property):
        """
        Checks if the given Property objects are equal

        :param object_: Given property object to check
        :param expected_value: expected property object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                self.check_attribute_equal(object_, 'value_type', expected_value.value_type) and
                self.check_attribute_equal(object_, 'value', expected_value.value) and
                self.check_attribute_equal(object_, 'value_id', expected_value.value_id))

    def _check_multi_language_property_equal(self, object_: model.MultiLanguageProperty,
                                             expected_value: model.MultiLanguageProperty):
        """
        Checks if the given MultiLanguageProperty objects are equal

        :param object_: Given MultiLanguageProperty object to check
        :param expected_value: expected MultiLanguageProperty object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                self.check_attribute_equal(object_, 'value', expected_value.value) and
                self.check_attribute_equal(object_, 'value_id', expected_value.value_id))

    def _check_range_equal(self, object_: model.Range, expected_value: model.Range):
        """
        Checks if the given Range objects are equal

        :param object_: Given Range object to check
        :param expected_value: expected Range object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                self.check_attribute_equal(object_, 'value_type', expected_value.value_type) and
                self.check_attribute_equal(object_, 'min_', expected_value.min_) and
                self.check_attribute_equal(object_, 'max_', expected_value.max_))

    def _check_blob_equal(self, object_: model.Blob, expected_value: model.Blob):
        """
        Checks if the given Blob objects are equal

        :param object_: Given Blob object to check
        :param expected_value: expected Blob object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                self.check_attribute_equal(object_, 'value', expected_value.value) and
                self.check_attribute_equal(object_, 'mime_type', expected_value.mime_type))

    def _check_file_equal(self, object_: model.File, expected_value: model.File):
        """
        Checks if the given File objects are equal

        :param object_: Given File object to check
        :param expected_value: expected File object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                self.check_attribute_equal(object_, 'value', expected_value.value) and
                self.check_attribute_equal(object_, 'mime_type', expected_value.mime_type))

    def _check_reference_element_equal(self, object_: model.ReferenceElement, expected_value: model.ReferenceElement):
        """
        Checks if the given ReferenceElement objects are equal

        :param object_: Given ReferenceElement object to check
        :param expected_value: expected ReferenceElement object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                self.check_attribute_equal(object_, 'value', expected_value.value))

    def _check_submodel_collection_equal(self, object_: model.SubmodelElementCollection,
                                         expected_value: model.SubmodelElementCollection):
        """
        Checks if the given SubmodelElementCollection objects are equal

        :param object_: Given SubmodelElementCollection object to check
        :param expected_value: expected SubmodelElementCollection object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        # TODO differ between ordered and unordered
        result = (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                  self.check_contained_element_length(object_, 'value', model.SubmodelElement,
                                                      len(expected_value.value)))
        for expected_element in expected_value.value:
            element = object_.value.get_referable(expected_element.id_short)
            result = result and self.check(element is not None, 'Submodel Element{} must '
                                                                'exist'.format(repr(expected_element)))

        for element in object_.value:
            expected_element = expected_value.value.get_referable(element.id_short)
            if expected_element:
                result = result and self._check_submodel_element(element, expected_element)
            else:
                self.check(expected_element is not None, 'Submodel Element{} must not exist'.format(repr(element)))
        return result

    def _check_relationship_element_equal(self, object_: model.RelationshipElement,
                                          expected_value: model.RelationshipElement):
        """
        Checks if the given RelationshipElement objects are equal

        :param object_: Given RelationshipElement object to check
        :param expected_value: expected RelationshipElement object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                self.check_attribute_equal(object_, 'first', expected_value.first) and
                self.check_attribute_equal(object_, 'second', expected_value.second))

    def _check_annotated_relationship_element_equal(self, object_: model.AnnotatedRelationshipElement,
                                                    expected_value: model.AnnotatedRelationshipElement):
        """
        Checks if the given AnnotatedRelationshipElement objects are equal

        :param object_: Given AnnotatedRelationshipElement object to check
        :param expected_value: expected AnnotatedRelationshipElement object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                self._check_relationship_element_equal(object_, expected_value) and
                self.check_attribute_equal(object_, 'annotation', expected_value.annotation))

    def _check_operation_variable_equal(self, object_: model.OperationVariable,
                                        expected_value: model.OperationVariable):
        """
        Checks if the given OperationVariable objects are equal

        :param object_: Given OperationVariable object to check
        :param expected_value: expected OperationVariable object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return self._check_submodel_element(object_.value, expected_value.value)

    def _check_operation_equal(self, object_: model.Operation, expected_value: model.Operation):
        """
        Checks if the given Operation objects are equal

        :param object_: Given Operation object to check
        :param expected_value: expected Operation object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        result = (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                  self.check_contained_element_length(object_, 'input_variable', model.OperationVariable,
                                                      len(expected_value.input_variable)) and
                  self.check_contained_element_length(object_, 'output_variable', model.OperationVariable,
                                                      len(expected_value.output_variable)) and
                  self.check_contained_element_length(object_, 'in_output_variable', model.OperationVariable,
                                                      len(expected_value.in_output_variable)))
        for i in range(len(object_.input_variable)):
            result = result and self._check_operation_variable_equal(object_.input_variable[i],
                                                                     expected_value.input_variable[i])
        for i in range(len(object_.output_variable)):
            result = result and self._check_operation_variable_equal(object_.output_variable[i],
                                                                     expected_value.output_variable[i])
        for i in range(len(object_.in_output_variable)):
            result = result and self._check_operation_variable_equal(object_.in_output_variable[i],
                                                                     expected_value.in_output_variable[i])
        return result

    def _check_capability_equal(self, object_: model.Capability, expected_value: model.Capability):
        """
        Checks if the given Capability objects are equal

        :param object_: Given Capability object to check
        :param expected_value: expected Capability object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return self._check_abstract_attributes_submodel_element_equal(object_, expected_value)

    def _check_entity_equal(self, object_: model.Entity, expected_value: model.Entity):
        """
        Checks if the given Entity objects are equal

        :param object_: Given Entity object to check
        :param expected_value: expected Entity object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        result = (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                  self.check_attribute_equal(object_, 'entity_type', expected_value.entity_type) and
                  self.check_attribute_equal(object_, 'asset', expected_value.asset) and
                  self.check_contained_element_length(object_, 'statement', model.SubmodelElement,
                                                      len(expected_value.statement)))
        for expected_element in expected_value.statement:
            element = object_.statement.get_referable(expected_element.id_short)
            result = result and self.check(element is not None, 'Entity{} must exist'.format(repr(expected_element)))

        for element in object_.statement:
            expected_element = expected_value.statement.get_referable(element.id_short)
            if expected_element:
                result = result and self._check_submodel_element(element, expected_element)
            else:
                self.check(expected_element is not None, 'Entity{} must not exist'.format(repr(element)))

        return result

    def _check_event_equal(self, object_: model.Event, expected_value: model.Event):
        """
        Checks if the given Event objects are equal

        :param object_: Given Event object to check
        :param expected_value: expected Event object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return self._check_abstract_attributes_submodel_element_equal(object_, expected_value)

    def _check_basic_event_equal(self, object_: model.BasicEvent, expected_value: model.BasicEvent):
        """
        Checks if the given BasicEvent objects are equal

        :param object_: Given BasicEvent object to check
        :param expected_value: expected BasicEvent object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self._check_abstract_attributes_submodel_element_equal(object_, expected_value) and
                self._check_event_equal(object_, expected_value) and
                self.check_attribute_equal(object_, 'observed', expected_value.observed))

    def check_submodel_equal(self, object_: model.Submodel, expected_value: model.Submodel):
        """
        Checks if the given Submodel objects are equal

        :param object_: Given Submodel object to check
        :param expected_value: expected Submodel object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        result = (self._check_identifiable_equal(object_, expected_value) and
                  self._check_has_semantics_equal(object_, expected_value) and
                  self._check_has_kind_equal(object_, expected_value) and
                  self._check_qualifiable_equal(object_, expected_value) and
                  self.check_contained_element_length(object_, 'submodel_element', model.SubmodelElement,
                                                      len(expected_value.submodel_element)))
        for expected_element in expected_value.submodel_element:
            element = object_.submodel_element.get_referable(expected_element.id_short)
            result = result and self.check(element is not None, 'Submodel Element{} must '
                                                                'exist'.format(repr(expected_element)))
        for element in object_.submodel_element:
            expected_element = expected_value.submodel_element.get_referable(element.id_short)
            if expected_element:
                result = result and self._check_submodel_element(element, expected_element)
            else:
                self.check(False, 'Submodel Element{} must not exist'.format(repr(element)))
        return result

    def _check_qualifier_equal(self, object_: model.Qualifier, expected_value: model.Qualifier):
        """
        Checks if the given Qualifier objects are equal

        :param object_: Given Qualifier object to check
        :param expected_value: expected Qualifier object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self.check_attribute_equal(object_, 'type_', expected_value.type_) and
                self.check_attribute_equal(object_, 'value_type', expected_value.value_type) and
                self.check_attribute_equal(object_, 'value', expected_value.value) and
                self.check_attribute_equal(object_, 'value_id', expected_value.value_id))

    def _check_formula_equal(self, object_: model.Formula, expected_value: model.Formula):
        """
        Checks if the given Formula objects are equal

        :param object_: Given Formula object to check
        :param expected_value: expected Formula object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return self.check_contained_element_length(object_, 'depends_on', model.Reference,
                                                   len(expected_value.depends_on))

    def check_asset_equal(self, object_: model.Asset, expected_value: model.Asset):
        """
        Checks if the given Asset objects are equal

        :param object_: Given Asset object to check
        :param expected_value: expected Asset object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self._check_identifiable_equal(object_, expected_value) and
                self.check_attribute_equal(object_, 'kind', expected_value.kind) and
                self.check_attribute_equal(object_, 'asset_identification_model',
                                           expected_value.asset_identification_model) and
                self.check_attribute_equal(object_, 'bill_of_material',
                                           expected_value.bill_of_material))

    def check_asset_administration_shell_equal(self, object_: model.AssetAdministrationShell,
                                               expected_value: model.AssetAdministrationShell):
        """
        Checks if the given AssetAdministrationShell objects are equal

        :param object_: Given AssetAdministrationShell object to check
        :param expected_value: expected AssetAdministrationShell object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        result = (self._check_identifiable_equal(object_, expected_value) and
                  self.check_attribute_equal(object_, 'asset', expected_value.asset) and
                  self._check_security_equal(object_.security_, expected_value.security_) and
                  self.check_attribute_equal(object_, 'derived_from', expected_value.derived_from) and
                  self.check_contained_element_length(object_, 'submodel_', model.AASReference,
                                                      len(expected_value.submodel_)) and
                  self.check_contained_element_length(object_, 'concept_dictionary', model.ConceptDictionary,
                                                      len(expected_value.concept_dictionary)) and
                  self.check_contained_element_length(object_, 'view', model.View,
                                                      len(expected_value.view)))
        for expected_ref in expected_value.submodel_:
            find = False
            for ref in object_.submodel_:
                if ref == expected_ref:
                    find = True
                    break
            if not find:
                result = result and self.check(False, 'Submodel Reference[{}] must be found'.format(repr(expected_ref)))

        for ref in object_.submodel_:
            find = False
            for expected_ref in expected_value.submodel_:
                if ref == expected_ref:
                    find = True
                    break
            if not find:
                result = result and self.check(False, 'Submodel Reference[{}] must not exist'.format(repr(ref)))

        for expected_element in expected_value.concept_dictionary:
            element = object_.concept_dictionary.get_referable(expected_element.id_short)
            result = result and self.check(element is not None, 'Concept Dictionary{} must '
                                                                'exist'.format(repr(expected_element)))

        for element in object_.concept_dictionary:
            expected_element = expected_value.concept_dictionary.get_referable(element.id_short)
            if expected_element:
                result = result and self._check_concept_dictionary_equal(element, expected_element)
            else:
                self.check(expected_element is not None, 'Concept Dictionary{} must not exist'.format(repr(element)))

        for expected_view in expected_value.view:
            view = object_.view.get_referable(expected_view.id_short)
            result = result and self.check(view is not None, 'View{} must exist'.format(repr(expected_view)))

        for view in object_.view:
            expected_view = expected_value.view.get_referable(view.id_short)
            if expected_view:
                result = result and self._check_view_equal(view, expected_view)
            else:
                self.check(expected_view is not None, 'View{} must not exist'.format(repr(view)))
        return result

    def _check_concept_dictionary_equal(self, object_: model.ConceptDictionary,
                                        expected_value: model.ConceptDictionary):
        """
        Checks if the given ConceptDictionary objects are equal

        :param object_: Given ConceptDictionary object to check
        :param expected_value: expected ConceptDictionary object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        result = (self._check_referable_equal(object_, expected_value) and
                  self.check_contained_element_length(object_, 'concept_description', model.AASReference,
                                                      len(expected_value.concept_description)))
        for expected_ref in expected_value.concept_description:
            find = False
            for ref in object_.concept_description:
                if ref == expected_ref:
                    find = True
                    break
            if not find:
                result = result and self.check(False, 'Concept Description Reference[{}] must be '
                                                      'found'.format(repr(expected_ref)))

        for ref in object_.concept_description:
            find = False
            for expected_ref in expected_value.concept_description:
                if ref == expected_ref:
                    find = True
                    break
            if not find:
                result = result and self.check(False, 'Concept Description Reference[{}] must not '
                                                      'exist'.format(repr(ref)))
        return result

    def _check_security_equal(self, object_: Optional[model.Security],
                              expected_value: Optional[model.Security]):
        """
        Checks if the given Security objects are equal

        :param object_: Given Security object to check
        :param expected_value: expected Security object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        # TODO: if security is specified
        return True

    def _check_view_equal(self, object_: model.View, expected_value: model.View):
        """
        Checks if the given View objects are equal

        :param object_: Given View object to check
        :param expected_value: expected View object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        result = (self._check_referable_equal(object_, expected_value) and
                  self._check_has_semantics_equal(object_, expected_value) and
                  self.check_contained_element_length(object_, 'contained_element', model.AASReference,
                                                      len(expected_value.contained_element)))

        for expected_ref in expected_value.contained_element:
            find = False
            for ref in object_.contained_element:
                if ref == expected_ref:
                    find = True
                    break
            if not find:
                result = result and self.check(False, 'Referable Element Reference[{}] must be '
                                                      'found'.format(repr(expected_ref)))

        for ref in object_.contained_element:
            find = False
            for expected_ref in expected_value.contained_element:
                if ref == expected_ref:
                    find = True
                    break
            if not find:
                result = result and self.check(False, 'Referable ELement Reference[{}] must not '
                                                      'exist'.format(repr(ref)))
        return result

    def check_concept_description_equal(self, object_: model.ConceptDescription,
                                        expected_value: model.ConceptDescription):
        """
        Checks if the given ConceptDescription objects are equal

        :param object_: Given ConceptDescription object to check
        :param expected_value: expected ConceptDescription object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        result = self._check_identifiable_equal(object_, expected_value)
        for expected_ref in expected_value.is_case_of:
            find = False
            for ref in object_.is_case_of:
                if ref == expected_ref:
                    find = True
                    break
            if not find:
                result = result and self.check(False, 'Referable Element Reference[{}] must be '
                                                      'found'.format(repr(expected_ref)))

        for ref in object_.is_case_of:
            find = False
            for expected_ref in expected_value.is_case_of:
                if ref == expected_ref:
                    find = True
                    break
            if not find:
                result = result and self.check(False, 'Referable ELement Reference[{}] must not '
                                                      'exist'.format(repr(ref)))
        if isinstance(expected_value, model.IEC61360ConceptDescription):
            if (self.check_is_instance(object_, model.IEC61360ConceptDescription)):
                self._check_iec61360_concept_description_equal(object_, expected_value)  # type: ignore
        return result

    def _check_iec61360_concept_description_equal(self, object_: model.IEC61360ConceptDescription,
                                                  expected_value: model.IEC61360ConceptDescription):
        """
        Checks if the given IEC61360ConceptDescription objects are equal

        :param object_: Given IEC61360ConceptDescription object to check
        :param expected_value: expected IEC61360ConceptDescription object
        :param kwargs: Relevant values to add to the check result for further analysis (e.g. the compared values)
        :return:
        """
        return (self.check_attribute_equal(object_, 'preferred_name', expected_value.preferred_name) and
                self.check_attribute_equal(object_, 'short_name', expected_value.short_name) and
                self.check_attribute_equal(object_, 'data_type', expected_value.data_type) and
                self.check_attribute_equal(object_, 'definition', expected_value.definition) and
                self.check_attribute_equal(object_, 'unit', expected_value.unit) and
                self.check_attribute_equal(object_, 'unit_id', expected_value.unit_id) and
                self.check_attribute_equal(object_, 'source_of_definition', expected_value.source_of_definition) and
                self.check_attribute_equal(object_, 'symbol', expected_value.symbol) and
                self.check_attribute_equal(object_, 'value_format', expected_value.value_format) and
                self.check_attribute_equal(object_, 'value_list', expected_value.value_list) and
                self.check_attribute_equal(object_, 'value', expected_value.value) and
                self.check_attribute_equal(object_, 'value_id', expected_value.value_id) and
                self.check_attribute_equal(object_, 'level_types', expected_value.level_types))

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
                          "{} must contain {} {}s".format(repr(object_), length, class_name.__name__),
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
