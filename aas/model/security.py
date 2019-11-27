
from typing import List
from enum import Enum, unique

from . import base, submodel


@unique
class PermissionKind(Enum):
    """
    Description of the kind of permission. Possible kind of permission also include the denial of the permission.

    Comment for devs: I found the enum members to be typically written in all caps, but couldn't verify this

    ALLOW: Allow the permission given to the subject
    DENY: Explicitly deny the permission given to the subject
    NOT_APPLICABLE: The permission is not applicable to the subject
    UNDEFINED: It is undefined whether the permission is allowed, not applicable or denied to the subject
    """
    ALLOW = 0
    DENY = 1
    NOT_APPLICABLE = 2
    UNDEFINED = 3


class Permission:
    """
    Description of a single permission

    :param permission: Reference to a property that defines the semantics of the permission
    :param kind_of_permission: Description of the kind of permission
    """
    def __init__(self,
                 permission: submodel.Property,
                 kind_of_permission: PermissionKind):

        self.permission: submodel.Property = permission
        self.kind_of_permission: PermissionKind = kind_of_permission


class ObjectAttribute:
    """
    A set of data elements that describe object attributes. These attributes need to refer to a data element within an
    existing submodel.

    Comment for devs: This deviates from the paper, as in the paper, there is a list of Object Attributes as its own
    class. I changed it, so that the list is now in the PermissionsPerObject class, as a list of instances of
    this class, as otherwise I'd add an extra class "ObjectAttributes" which seems extra to me.

    :param object_attribute: A data elements that further classifies an object.
    """
    def __init__(self,
                 object_attribute: submodel.Property):

        self.object_attribute: submodel.Property = object_attribute


class PermissionsPerObject:
    """
    Defines access permissions for a specified object.

    The object is any referable element in the AAS. Additionally object attributes can be defined that further specify
    the kind of object the permissions apply to.

    :param permission_object: Element to which permission shall be assigned
    :param target_object_attributes: Target object attributes that need to be fulfilled so that the access permissions
                                     apply to the accessing subject.
    :param permissions: Permissions assigned to the object. The permissions hold for all subjects as specified in the
                        access permission rule.
    """
    def __init__(self,
                 permission_object: base.Referable,
                 target_object_attributes: List[ObjectAttribute],
                 permissions: List[Permission]):

        self.permission_object: base.Referable = permission_object
        self.target_object_attributes: List[ObjectAttribute] = target_object_attributes
        self.permissions: List[Permission] = permissions


class SubjectAttribute:
    """
    A list of data elements that further classifies a specific subject

    :param subject_attribute: A data element that further classifies a specific subject.
    """
    def __init__(self,
                 subject_attribute: submodel.Property):

        self.subject_attribute: submodel.Property = subject_attribute


class AccessPermissionRule(base.Referable, base.Qualifiable):
    """
    Table that defines access permissions per authenticated subject for a set of objects (referable elements)

    :param target_subject_attributes: List of instances of the class SubjectAttribute
                                      Target subject attributes that need to be fulfilled by the accessing subject to
                                      get the permissions defined by this rule.
    :param permissions_per_object: List of instances of the class PermissionsPerObject
                                   Set of object-permission pairs that define the permissions per object within the
                                   access permission rule
    """
    def __init__(self,
                 target_subject_attributes: List[SubjectAttribute],
                 permissions_per_object: List[PermissionsPerObject]):

        super().__init__()
        self.target_subject_attributes: List[SubjectAttribute] = target_subject_attributes
        self.permissions_per_object: List[PermissionsPerObject] = permissions_per_object


class AccessControl:
    """
    Defines the local access control policy administration point, has the major task of defining the access permission
    rules.

    The policy decision point of access control as realized by the AAS itself

    :param selectable_subject_attributes: Reference to a submodel defining the authenticated subjects to access elements
                                          that are configured for the AAS. They are selectable by the access permission
                                          rules to assign permissions to the subjects.
                                          TODO: Default: refer to submodel of default_subject_attributes
    :param default_subject_attributes: Reference to a submodel defining the default subjects
                                       attributes for the AAS that can be used to describe
                                       access permission rules.
    :param selectable_permissions: Reference to a submodel defining which permissions
                                   can be assigned to the subjects
                                   TODO: Default: refer to submodel of default_permissions
    :param default_permissions: Reference to a submodel defining the default
                                permissions for the AAS.
    :param selectable_environment_attributes: Reference to a submodel defining which environment
                                              attributes can be accessed via the permission rules
                                              defined for the AAS, i.e. attributes that are not
                                              describing the asset itself.
                                              TODO: Default refer to default_environment_attributes
    :param default_environment_attributes: Reference to a submodel defining default environment
                                           attributes, i.e. attributes that are not describing the
                                           asset itself.
    :param access_permission_rules: List of instances of the class AccessPermissionRule
                                    Access permission rules of the AAS describing the rights assigned to (already
                                    authenticated) subjects to access elements of the AAS
    """

    def __init__(self,
                 selectable_subject_attributes: submodel.Submodel,
                 default_subject_attributes: submodel.Submodel,
                 selectable_permissions: submodel.Submodel,
                 default_permissions: submodel.Submodel,
                 selectable_environment_attributes: submodel.Submodel,
                 default_environment_attributes: submodel.Submodel,
                 access_permission_rules: List[AccessPermissionRule]):

        self.selectable_subject_attributes: submodel.Submodel = selectable_subject_attributes
        self.default_subject_attributes: submodel.Submodel = default_subject_attributes
        self.selectable_permissions: submodel.Submodel = selectable_permissions
        self.default_permissions: submodel.Submodel = default_permissions
        self.selectable_environment_attributes: submodel.Submodel = selectable_environment_attributes
        self.default_environment_attributes: submodel.Submodel = default_environment_attributes
        self.access_permission_rules: List[AccessPermissionRule] = access_permission_rules


class Endpoint:
    """
    Endpoint to an external access control defining a policy administration point to be used by the AAS

    not yet specified in the current Metamodel
    """
    pass


class PolicyAdministrationPoint:
    """
    Definition of a security administration point (PDP)

    :param access_control: Instance of Access Control (optional)
    :param endpoint: Instance of Endpoint (optional)
    """
    def __init__(self,
                 access_control: AccessControl,
                 endpoint: Endpoint):

        self.local_access_control: AccessControl = access_control
        self.external_access_control = endpoint


class PolicyDecisionPoint:
    """
    Computes access decisions by evaluating the applicable Digital Policies and Meta-Policies. One of the main functions
    of the PDP is to mediate or de-conflict Digital Policies according to Meta-Policies
    TODO: Find definition from [22]
    """
    pass


class PolicyEnforcementPoint:
    """
    TODO: Find anything about this class

    """
    pass


class PolicyInformationPoints:
    """
    Defines the security policy information points (PIP)

    Serves as the retrieval attributes, or the data required for policy evaluation to provide the information needed
    by the policy decision point to make the decisions.

    :param external_information_point_list: List of endpoints to external available information points taking into consideration for
                                       access control for the AAS (optional)
    :param internal_information_point_list: List of references to submodels defining information used by security
                                            access permission rules (optional)
    """
    def __init__(self,
                 external_information_point_list: List[Endpoint],
                 internal_information_point_list: List[submodel.Submodel]):
        self.external_information_point_list: List[Endpoint] = external_information_point_list
        self.internal_information_point_list: List[submodel.Submodel] = internal_information_point_list


class AccessControlPolicyPoints:
    """
    Container for access control policy points

    :param policy_administration_point: Instance of PolicyAdministrationPoint (mandatory)
    :param policy_decision_point: Instance of PolicyDecisionPoint (mandatory)
    :param policy_enforcement_point: Instance of PolicyEnforcementPoint (mandatory)
    :param policy_information_points: Instance of PolicyInformationPoints (optional)
    """
    def __init__(self,
                 policy_administration_point: PolicyAdministrationPoint,
                 policy_decision_point: PolicyDecisionPoint,
                 policy_enforcement_point: PolicyEnforcementPoint,
                 policy_information_points: PolicyInformationPoints):

        self.policy_administration_point: PolicyAdministrationPoint = policy_administration_point
        self.policy_decision_point: PolicyDecisionPoint = policy_decision_point
        self.policy_enforcement_point: PolicyEnforcementPoint = policy_enforcement_point
        self.policy_information_points: PolicyInformationPoints = policy_information_points


class Certificate:
    """
    Certificate is not yet further defined
    """
    pass


class Security:
    """
    Container for security relevant information of the AAS.

    :param access_control_policy_point: Instance of the PolicyAdministrationPoint Class (mandatory)
    :param trust_anchor_list: List of used certificates (optional)
    """
    def __init__(self,
                 access_control_policy_point: AccessControlPolicyPoints,
                 trust_anchor_list: List[Certificate]):

        self.access_control_policy_point: AccessControlPolicyPoints = access_control_policy_point
        self.trust_anchor_list: List[Certificate] = trust_anchor_list
