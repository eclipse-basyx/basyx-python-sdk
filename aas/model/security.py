
from typing import List
from enum import Enum, auto

#Todo: Resolve missing references for:
"""
Property, Referable
"""

class PermissionKind(Enum):
    """
    Description of the kind of permission. Possible kind of permission also include the denial of the permission.

    Comment for devs: I found the enum members to be typically written in all caps, but couldn't verify this

    :var ALLOW: Allow the permission given to the subject
    :var DENY: Explicitly deny the permission given to the subject
    :var NOT_APPLICABLE: The permission is not applicable to the subject
    :var UNDEFINED: It is undefined whether the permission is allowed, not applicable or denied to the subject
    """
    ALLOW = auto()
    DENY = auto()
    NOT_APPLICABLE = auto()
    UNDEFINED = auto()

class Permission:
    """
    Description of a single permission

    @:param permission: Reference to a property that defines the semantics of the permission
    @:param kind_of_permission: Description of the kind of permission
    """
    def __init__(self, permission: isinstance(Property),
                 kind_of_permission: isinstance(PermissionKind)):

        self.permission: isinstance(Property) = permission
        self.kind_of_permission: isinstance(PermissionKind) = kind_of_permission


class ObjectAttribute:
    """
    A set of data elements that describe object attributes. These attributes need to refer to a data element within an
    existing submodel.

    Comment for devs: This deviates from the paper, as in the paper, there is a list of Object Attributes as its own
    class. I changed it, so that the list is now in the PermissionsPerObject class, as a list of instances of
    this class, as otherwise I'd add an extra class "ObjectAttributes" which seems extra to me.

    @:param object_attribute: Property (mandatory)
    """
    def __init__(self, object_attribute: isinstance(Property)):

        self.object_attribute: isinstance(Property) = object_attribute


class PermissionsPerObject:
    """
    Defines access permissions for a specified object.

    The object is any referable element in the AAS. Additionally object attributes can be defined that further specify
    the kind of object the permissions apply to.

    @:param permission_object: Instance of class Referable (mandatory)
    @:param target_object_attributes: List of instances of ObjectAttribute (can be empty)
    @:param permissions: List of instances of the class Permission (optional)
    """
    def __init__(self, permission_object: isinstance(Referable),
                 target_object_attributes: List[ObjectAttribute],
                 permissions: List[Permission]):

        self.permission_object: isinstance(Referable) = permission_object
        self.target_object_attributes: List[ObjectAttribute] = target_object_attributes
        self.permissions: List[Permission] = permissions


class SubjectAttribute:
    """
    A list of data elements that further classifies a specific subject

    @:param subject_attributes: List of Properties (needs at least one entry)
    """
    def __init__(self, subject_attribute: isinstance(Property)):

        self.subject_attribute: isinstance(Property) = subject_attribute


class AccessPermissionRule:
    """
    Table that defines access permissions per authenticated subject for a set of objects (referable elements)

    @:param target_subject_attributes: List of instances of the class SubjectAttribute (needs at least one entry)
    @:param permissions_per_object: List of instances of the class PermissionsPerObject (optional)
    """
    def __init__(self, target_subject_attributes: List[SubjectAttribute],
                 permissions_per_object: List[PermissionsPerObject]):

        self.target_subject_attributes: List[SubjectAttribute] = target_subject_attributes
        self.permissions_per_object: List[PermissionsPerObject] = permissions_per_object


class AccessControl:
    """
    Access Control of the Policy Administration Point

    :param selectable_subject_attributes: Submodel of the selectable subject attributes
    :param default_subject_attributes: Submodel of the default subject attributes
    :param selectable_permissions: Submodel of the selectable permissions
    :param default_permissions: Submodel of the default permissions
    :param selectable_environment_attributes: Submodel of the selectable environment attributes (optional)
    :param default_environment_attributes: Submodel of the default environment attributes (optional)
    :param access_permission_rules: List of instances of the class AccessPermissionRule (can be empty)
    """

    def __init__(self, selectable_subject_attributes: isinstance(Submodel),
                 default_subject_attributes: isinstance(Submodel),
                 selectable_permissions: isinstance(Submodel),
                 default_permissions: isinstance(Submodel),
                 selectable_environment_attributes: isinstance(Submodel),
                 default_environment_attributes: isinstance(Submodel),
                 access_permission_rules: List[AccessPermissionRule]):

        self.selectable_subject_attributes: isinstance(Submodel) = selectable_subject_attributes
        self.default_subject_attributes: isinstance(Submodel) = default_subject_attributes
        self.selectable_permissions: isinstance(Submodel) = selectable_permissions
        self.default_permissions: isinstance(Submodel) = default_permissions
        self.selectable_environment_attributes: isinstance(Submodel) = selectable_environment_attributes
        self.default_environment_attributes: isinstance(Submodel) = default_environment_attributes
        self.access_permission_rules: List[AccessPermissionRule] = access_permission_rules


class Endpoint:
    """
    not yet specified in the current Metamodel
    """
    pass


class PolicyAdministrationPoint:
    """
    Handles Access Control to the AAS, including local and external access

    :param access_control: local access control
    :param endpoint: external access control
    """
    def __init__(self, access_control: isinstance(AccessControl),
                 endpoint: isinstance(Endpoint)):

        self.local_access_control: isinstance(AccessControl) = access_control
        self.external_access_control = endpoint


class Security:
    """
    Security Models of the AAS

    Security includes the PolicyAdministrationPoint, but is not limited to it, things may be added later.

    :param policy_administration_point: Instance of the PolicyAdministrationPoint Class
    """
    def __init__(self, policy_administration_point: isinstance(PolicyAdministrationPoint)):

        self.policy_administration_point: isinstance(PolicyAdministrationPoint) = policy_administration_point
