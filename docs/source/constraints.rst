Metamodel-Constraints
=====================

Here is a quick reference of the constraints as defined in Details of the AssetAdministrationShell Part 1
and how they are implemented in the Eclipse BaSyx Python SDK.


The status information means the following:

* ✅: the Constraint is enforced in the current version
* ❌: the Constraint cannot be enforced in the current version
* WIP: The Constraint enforcement will be implemented in the future

In most cases, if a constraint violation is detected,
an :class:`~basyx.aas.model.base.AASConstraintViolation` will be raised

.. |aasd002| replace:: ``idShort`` of ``Referable`` s shall only feature letters, digits, underscore (``_``); starting mandatory with a letter, i.e. ``[a-zA-Z][a-zA-Z0-9_]*``.
.. |aasd005| replace:: If ``AdministrativeInformation/version`` is not specified, ``AdministrativeInformation/revision`` shall also be unspecified. This means that a revision requires a version. If there is no version, there is no revision. Revision is optional.
.. |aasd006| replace:: If both, the ``value`` and the ``valueId`` of a ``Qualifier`` are present, the value needs to be identical to the value of the referenced coded value in ``Qualifier/valueId``.
.. |aasd007| replace:: If both the ``Property/value`` and the ``Property/valueId`` are present, the value of ``Property/value`` needs to be identical to the value of the referenced coded value in ``Property/valueId``.
.. |aasd012| replace:: if both the ``MultiLanguageProperty/value`` and the ``MultiLanguageProperty/valueId`` are present, the meaning must be the same for each string in a specific language, as specified in ``MultiLanguageProperty/valueId``.
.. |aasd014| replace:: Either the attribute ``globalAssetId`` or ``specificAssetId`` of an ``Entity`` must be set if ``Entity/entityType`` is set to ``SelfManagedEntity``. Otherwise, they do not exist.
.. |aasd020| replace:: The value of ``Qualifier/value`` shall be consistent with the data type as defined in ``Qualifier/valueType``.
.. |aasd021| replace:: Every qualifiable can only have one qualifier with the same ``Qualifier/type``.
.. |aasd022| replace:: ``idShort`` of non-identifiable referables within the same name space shall be unique (case-sensitive).
.. |aasd077| replace:: The name of an extension (``Extension/name``) within ``HasExtensions`` needs to be unique.
.. |aasd080| replace:: In case ``Key/type`` == ``GlobalReference`` ``idType`` shall not be any LocalKeyType (``IdShort, FragmentId``).
.. |aasd081| replace:: In case ``Key/type`` == ``AssetAdministrationShell`` ``Key/idType`` shall not be any LocalKeyType (``IdShort``, ``FragmentId``).
.. |aasd090| replace:: for data elements, ``category`` (inherited by ``Referable``) shall be one of the following values: CONSTANT, PARAMETER or VARIABLE. Default: VARIABLE
.. |aasd107| replace:: If a first level child element in a ``SubmodelElementList`` has a semanticId, it shall be identical to ``SubmodelElementList/semanticIdListElement``.
.. |aasd108| replace:: All first level child elements in a ``SubmodelElementList`` shall have the same submodel element type as specified in ``SubmodelElementList/typeValueListElement``.
.. |aasd109| replace:: If ``SubmodelElementList/typeValueListElement`` is equal to ``Property`` or ``Range,`` ``SubmodelElementList/valueTypeListElement`` shall be set and all first level child elements in the ``SubmodelElementList`` shall have the value type as specified in ``SubmodelElementList/valueTypeListElement``.
.. |aasd114| replace:: If two first level child elements in a ``SubmodelElementList`` have a ``semanticId``, they shall be identical.
.. |aasd115| replace:: If a first level child element in a ``SubmodelElementList`` does not specify a ``semanticId``, the value is assumed to be identical to ``SubmodelElementList/semanticIdListElement``.
.. |aasd116| replace:: ``globalAssetId`` (case-insensitive) is a reserved key. If used as value for ``SpecificAssetId/name,`` ``SpecificAssetId/value`` shall be identical to ``AssetInformation/globalAssetId``.
.. |aasd117| replace:: ``idShort`` of non-identifiable ``Referables`` not being a direct child of a ``SubmodelElementList`` shall be specified.
.. |aasd118| replace:: If a supplemental semantic ID (``HasSemantics/supplementalSemanticId``) is defined, there shall also be a main semantic ID (``HasSemantics/semanticId``).
.. |aasd119| replace:: If any ``Qualifier/kind`` value of a ``Qualifiable/qualifier`` is equal to ``TemplateQualifier`` and the qualified element inherits from ``HasKind``, the qualified element shall be of kind ``Template`` (``HasKind/kind = Template``).
.. |aasd120| replace:: ``idShort`` of submodel elements being a direct child of a ``SubmodelElementList`` shall not be specified.
.. |aasd121| replace:: For ``References``, the value of ``Key/type`` of the first ``key`` of ``Reference/keys`` shall be one of ``GloballyIdentifiables``.
.. |aasd122| replace:: For external references, i.e. ``References`` with ``Reference/type = ExternalReference``, the value of ``Key/type`` of the first key of ``Reference/keys`` shall be one of ``GenericGloballyIdentifiables``.
.. |aasd123| replace:: For model references, i.e. ``References`` with ``Reference/type = ModellReference``, the value of ``Key/type`` of the first ``key`` of ``Reference/keys`` shall be one of ``AasIdentifiables``.
.. |aasd124| replace:: For external references, i.e. ``References`` with ``Reference/type = ExternalReference``, the last ``key`` of ``Reference/keys`` shall be either one of ``GenericGloballyIdentifiables`` or one of ``GenericFragmentKeys``.
.. |aasd125| replace:: For model references, i.e. ``References`` with ``Reference/type`` = ``ModelReference`` with more than one key in ``Reference/keys,`` the value of ``Key/type`` of each of the keys following the first key of ``Reference/keys`` shall be one of ``FragmentKeys``.
.. |aasd126| replace:: For model references, i.e. ``References`` with ``Reference/type = ModelReference`` with more than one key in ``Reference/keys,`` the value of ``Key/type`` of the last ``Key`` in the reference key chain may be one of ``GenericFragmentKeys`` or no key at all shall have a value out of ``GenericFragmentKeys``.
.. |aasd127| replace:: For model references, i.e. ``References`` with ``Reference/type = ModelReference`` with more than one key in ``Reference/keys,`` a key with ``Key/type`` ``FragmentReference`` shall be preceded by a key with ``Key/type`` ``File`` or ``Blob``. All other Asset Administration Shell fragments, i.e. ``Key/type`` values out of ``AasSubmodelElements``, do not support fragments.
.. |aasd128| replace:: For model references, i.e. ``References`` with ``Reference/type = ModelReference``, the ``Key/value`` of a ``Key`` preceded by a ``Key`` with ``Key/type=SubmodelElementList`` is an integer number denoting the position in the array of the submodel element list.
.. |aasd129| replace:: If any ``Qualifier/kind`` value of a ``SubmodelElement/qualifier`` (attribute ``qualifier`` inherited via ``Qualifiable``) is equal to ``TemplateQualifier``, the submodel element shall be part of a submodel template, i.e. a ``Submodel`` with ``Submodel/kind`` (attribute ``kind`` inherited via ``HasKind``) value equal to ``Template``.
.. |aasd130| replace:: An attribute with data type ``string`` shall consist of these characters only: ``^[\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\u00010000-\u0010FFFF]*$``.
.. |aasd131| replace:: The ``globalAssetId`` or at least one ``specificAssetId`` shall be defined for ``AssetInformation``.
.. |aasd133| replace:: ``SpecificAssetId/externalSubjectId`` shall be a global reference, i.e. ``Reference/type = ExternalReference``.
.. |aasd134| replace:: For an ``Operation,`` the ``idShort`` of all ``inputVariable/value``, ``outputVariable/value,`` and ``inoutputVariable/value`` shall be unique.

.. |aasc003| replace:: For a ``ConceptDescription`` with ``category`` VALUE using data specification template IEC61360 ``DataSpecificationIEC61360/value`` shall be set.
.. |aasc004| replace:: For a ``ConceptDescription`` with ``category`` PROPERTY or VALUE using data specification template IEC61360 - ``DataSpecificationIEC61360/dataType`` is mandatory and shall be defined.
.. |aasc005| replace:: For a ``ConceptDescription`` with ``category`` REFERENCE using data specification template IEC61360 - ``DataSpecificationIEC61360/dataType`` is STRING by default.
.. |aasc006| replace:: For a ``ConceptDescription`` with ``category`` DOCUMENT using data specification template IEC61360 - ``DataSpecificationIEC61360/dataType`` shall be one of the following values: STRING or URL.
.. |aasc007| replace:: For a ``ConceptDescription`` with ``category`` QUALIFIER_TYPE using data specification template IEC61360 - ``DataSpecificationIEC61360/dataType`` is mandatory and shall be defined.
.. |aasc008| replace:: For a ConceptDescriptions except for a ``ConceptDescription`` of ``category`` VALUE using data specification template IEC61360 - ``DataSpecificationIEC61360/definition`` is mandatory and shall be defined at least in English.
.. |aasc009| replace:: If ``DataSpecificationIEC61360/dataType`` one of: INTEGER_MEASURE, REAL_MEASURE, RATIONAL_MEASURE, INTEGER_CURRENCY, REAL_CURRENCY, then ``DataSpecificationIEC61360/unit`` or ``DataSpecificationIEC61360/unitId`` shall be defined.
.. |aasc010| replace:: If ``DataSpecificationIEC61360/value`` is not empty then ``DataSpecificationIEC61360/valueList`` shall be empty and vice versa.


..  csv-table::
    :header: "Constraint", "Description", "Status", "Comment"

    AASd-002, |aasd002|, ✅,
    AASd-005, |aasd005|, ✅,
    AASd-006, |aasd006|, ❌, Uncheckable; cannot check the value of what value_id points to
    AASd-007, |aasd007|, ❌, Uncheckable; cannot check the value of what value_id points to
    AASd-012, |aasd012|, ❌, Uncheckable
    AASd-014, |aasd014|, ✅,
    AASd-020, |aasd020|, ✅,
    AASd-021, |aasd021|, ✅,
    AASd-022, |aasd022|, ✅,
    AASd-077, |aasd077|, ✅,
    AASd-080, |aasd080|, ✅,
    AASd-081, |aasd081|, ✅,
    AASd-090, |aasd090|, ✅,
    AASd-107, |aasd107|, ✅,
    AASd-108, |aasd108|, ✅,
    AASd-109, |aasd109|, ✅,
    AASd-114, |aasd114|, ✅,
    AASd-115, |aasd115|, ❌, postponed
    AASd-116, |aasd116|, ❌, postponed
    AASd-117, |aasd117|, ✅,
    AASd-118, |aasd118|, ✅,
    AASd-119, |aasd119|, ❌, See `#119 <https://github.com/eclipse-basyx/basyx-python-sdk/issues/119>`__
    AASd-120, |aasd120|, ✅,
    AASd-121, |aasd121|, ✅,
    AASd-122, |aasd122|, ✅,
    AASd-123, |aasd123|, ✅,
    AASd-124, |aasd124|, ✅,
    AASd-125, |aasd125|, ✅,
    AASd-126, |aasd126|, ✅,
    AASd-127, |aasd127|, ✅,
    AASd-128, |aasd128|, ✅,
    AASd-129, |aasd129|, ❌, See `#119 <https://github.com/eclipse-basyx/basyx-python-sdk/issues/119>`__
    AASd-130, |aasd130|, ✅, Here a :class:`ValueError` instead of :class:`~basyx.aas.model.base.AASConstraintViolation` will be raised.
    AASd-131, |aasd131|, ✅,
    AASd-133, |aasd133|, ✅, Enforced by the typechecker. See `#119 <https://github.com/eclipse-basyx/basyx-python-sdk/pull/147>`__
    AASd-134, |aasd134|, ✅,
    AASc-003, |aasc003|, tbd
    AASc-004, |aasc004|, tbd
    AASc-005, |aasc005|, tbd
    AASc-006, |aasc006|, tbd
    AASc-007, |aasc007|, tbd
    AASc-008, |aasc008|, tbd
    AASc-009, |aasc009|, tbd
    AASc-010, |aasc010|, tbd
