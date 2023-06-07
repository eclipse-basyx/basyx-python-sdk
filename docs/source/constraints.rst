Metamodel-Constraints
=====================

Here is a quick reference of the constraints as defined in Details of the AssetAdministrationShell Part 1
and how they are implemented in the Eclipse BaSyx Python SDK.


The status information means the following:

* ✅: the Constraint is enforced in the current version
* ❌: the Constraint cannot be enforced in the current version
* WIP: The Constraint enforcement will be implemented in the future

In most cases, if a constraint violation is detected,
an :class:`~aas.model.base.AASConstraintViolation` will be raised

=========== =================================== ====== ===================================
Constraint  Description                         Status Comment
=========== =================================== ====== ===================================
AASd-002    `Referable.id_short` shall only     ✅
            contain
            \[a-zA-Z\]\[\a\-zA\-Z0\-\9_\]

            and
            must start with a letter
AASd-003    `Referable.id_short` shall be       WIP    See
            matched case-insensitive                   `#117 <https://git.rwth-aachen.de/
                                                       acplt/pyi40aas/-/issues/117>`_
AASd-005    A revision requires a version.      ✅

            This means, if there is no
            version there is no
            revision either.
AASd-006    If both, the value and the valueId
            of a Qualifier are present,
            the value needs to be identical to
            the value of the referenced coded
            value in Qualifier/valueId.
AASd-007    If both, the value and the valueId  ❌     Uncheckable, cannot check the value
            of a Qualifier are present, the            of what value_id points to
            value needs to be identical to the
            value of the referenced coded value
            in Qualifier/valueId.
AASd-008    The submodel element value of an    ✅
            operation variable shall be

            of kind=Template.
AASd-012    if both the                         ❌     Uncheckable
            MultiLanguageProperty/value and
            the MultiLanguageProperty/valueId
            are present, the meaning must be
            the same for each string in a
            specific language, as specified in
            MultiLanguageProperty/valueId.
AASd-014    Either the attribute globalAssetId  ✅
            or specificAssetId of an

            Entity
            must be set if Entity/entityType
            is set to

            “SelfManagedEntity”.
            They are not existing otherwise.
AASd-020    The value of Qualifier/value shall  ✅
            be consistent with the data type
            as defined in Qualifier/valueType.
AASd-021    Every Qualifiable can only have     WIP    postponed
            one qualifier with the same

            Qualifier/type.
AASd-022    idShort of                          ✅
            non-identifiable Referables

            shall be unique in its
            namespace.
AASd-023    AssetInformation/globalAssetId      ❌     Uncheckable, cannot resolve
            either is a reference to an

            Asset object or a global reference
AASd-026    If allowDuplicates==false then it   WIP    See `#118
                                                       <https://git.rwth-aachen.de/
                                                       acplt/pyi40aas/-/issues/117>`_
            is not allowed that the
            collection contains several
            elements

            with the same
            semantics (i.e. the same
            semanticId).
AASd-051    A ConceptDescription shall have     ✅
            one of the following

            categories:
            VALUE, PROPERTY, REFERENCE,

            DOCUMENT, CAPABILITY,
            RELATIONSHIP,

            COLLECTION,
            FUNCTION, EVENT, ENTITY,

            APPLICATION_CLASS, QUALIFIER,
            VIEW.

            Default: PROPERTY.
AASd-052a   If the semanticId of a Property     ❌     Uncheckable, semantic_id may not
                                                       be resolvable
            references a ConceptDescription
            then the

            ConceptDescription/category shall
            be one of following

            values: VALUE, PROPERTY.
AASd-052b   If the semanticId of a              ❌     Uncheckable, semantic_id may not
            MultiLanguageProperty                      be resolvable

            references
            a ConceptDescription then the

            ConceptDescription/category shall
            be one of following

            values: PROPERTY.
AASd-053    If the semanticId of a Range        ❌     Uncheckable, semantic_id may not
            submodel element                           be resolvable

            references a ConceptDescription
            then the

            ConceptDescription/category shall
            be one of following

            values: PROPERTY.
AASd-054    If the semanticId of a              ❌     Uncheckable, semantic_id may not
            ReferenceElement                           be resolvable

            submodel element references a
            ConceptDescription then the

            ConceptDescription/category shall
            be one of following

            values: REFERENCE.
AASd-055    If the semanticId of a              ❌     Uncheckable, semantic_id may not
            RelationshipElement or an                  be resolvable

            AnnotatedRelationshipElement
            submodel element

            references a
            ConceptDescription then the

            ConceptDescription/category shall
            be one of following

            values: RELATIONSHIP
AASd-056    If the semanticId of a Entity       ❌     Uncheckable, semantic_id may not
            submodel element                           be resolvable

            references a ConceptDescription
            then the

            ConceptDescription/category shall
            be one of following

            values: ENTITY.

            The ConceptDescription describes
            the elements assigned to the

            entity via Entity/statement.
AASd-057    The semanticId of a File or Blob    ❌     Uncheckable, semantic_id may not
            submodel element shall only                be resolvable

            reference a ConceptDescription
            with the category DOCUMENT.
AASd-058    If the semanticId of a Capability   ❌     Uncheckable, semantic_id may not
            submodel element                           be resolvable

            references a ConceptDescription
            then the

            ConceptDescription/category shall
            be CAPABILITY.
AASd-059    If the semanticId of a              ❌     Uncheckable, semantic_id may not
            SubmodelElementCollection                  be resolvable

            references a ConceptDescription
            then the category of the

            ConceptDescription shall be
            COLLECTION or ENTITY.
AASd-060    If the semanticId of a Operation    ❌     Uncheckable, semantic_id may not
            submodel element                           be resolvable

            references a ConceptDescription
            then the category of the

            ConceptDescription shall be one
            of the following

            values: FUNCTION.
AASd-061    If the semanticId of an             ❌     Uncheckable, semantic_id may not
            EventElement submodel element              be resolvable

            references a ConceptDescription
            then the category of the

            ConceptDescription shall be one
            of the following: EVENT.
AASd-062    If the semanticId of a Property     ❌     Uncheckable, semantic_id may not
            references a ConceptDescription            be resolvable

            then the
            ConceptDescription/category
            shall be one of following

            values: APPLICATION_CLASS.
AASd-063    If the semanticId of a Qualifier    ❌     Uncheckable, semantic_id may not
            references a ConceptDescription            be resolvable

            then the
            ConceptDescription/category shall
            be one of following

            values: QUALIFIER.
AASd-064    If the semanticId of a View         ❌     Uncheckable, semantic_id may not
            references a ConceptDescription            be resolvable

            then the category of the
            ConceptDescription shall

            be VIEW.
AASd-065    If the semanticId of a Property     ❌     Uncheckable, semantic_id may not
            or MultiLanguageProperty                   be resolvable

            references a ConceptDescription
            with the category VALUE

            then the value of the property
            is identical to

            DataSpecificationIEC61360/value
            and the valueId of the property

            is identical to
            DataSpecificationIEC61360/valueId.
AASd-066    If the semanticId of a Property     ❌     Uncheckable, semantic_id may not
            or MultiLanguageProperty                   be resolvable

            references a ConceptDescription
            with the category

            PROPERTY and
            DataSpecificationIEC61360/
            valueList is

            defined the value and valueId of
            the property is identical

            to one
            of the value reference pair types
            references in the value list,

            i.e. ValueReferencePairType/value
            or

            ValueReferencePairType/valueId,
            resp.
AASd-067    If the semanticId of a              ❌     Uncheckable, semantic_id may not
            MultiLanguageProperty                      be resolvable

            references a ConceptDescription
            then

            DataSpecificationIEC61360/dataType
            shall be

            STRING_TRANSLATABLE.
AASd-068    If the semanticId of a Range        ❌     Uncheckable, semantic_id may not
            submodel element                           be resolvable

            references a ConceptDescription
            then

            DataSpecificationIEC61360/dataType
            shall be a numerical one,

            i.e. REAL_* or RATIONAL_*.
AASd-069    If the semanticId of a Range        ❌     Uncheckable, semantic_id may not
            references a                               be resolvable

            ConceptDescription then
            DataSpecificationIEC61360/
            levelType

            shall be identical to the set
            {Min, Max}.
AASd-070    For a ConceptDescription with       tbd
            category PROPERTY or VALUE

            using data specification
            template IEC61360 -

            DataSpecificationIEC61360/dataType
            is mandatory and shall be

            defined.
AASd-071    For a ConceptDescription with       tbd
            category REFERENCE

            using data specification template
            IEC61360 -

            DataSpecificationIEC61360/dataType
            is STRING by default.
AASd-072    For a ConceptDescription with       tbd
            category DOCUMENT

            using data specification template
            IEC61360 -

            DataSpecificationIEC61360/dataType
            shall be one of the following

            values: STRING or URL.
AASd-073    For a ConceptDescription with       tbd
            category QUALIFIER

            using data specification template
            IEC61360 -

            DataSpecificationIEC61360/dataType
            is mandatory and shall be

            defined.
AASd-074    For all ConceptDescriptions except  tbd
            for ConceptDescriptions

            of category VALUE
            using data specification template
            IEC61360 -

            DataSpecificationIEC61360/
            definition is mandatory
            and shall be

            defined at least in English.
AASd-075    For all ConceptDescriptions         tbd
            using data specification template

            IEC61360 values for the attributes
            not being marked as

            mandatory or
            optional in tables

            Table 7,
            Table 8, Table 9 and Table 10

            depending on its category are
            ignored and handled as undefined.
AASd-076    For all ConceptDescriptions         tbd
            using data specification template

            IEC61360 at least a preferred
            name in English shall be defined.
AASd-77     The name of an extension within     tbd
            HasExtensions needs to be unique.
AASd-080    In case Key/type ==                 ✅
            GlobalReference,

            idType shall not be any
            LocalKeyType (IdShort, FragmentId)
AASd-081    In case                             ✅
            Key/type==AssetAdministrationShell

            Key/idType shall not be any
            LocalKeyType (IdShort, FragmentId)
AASd-090    For data elements                   ✅
            DataElement/category shall be one

            of the following values:

            CONSTANT, PARAMETER or
            VARIABLE.

            Exception: File and Blob data
            elements
AASd-092    If the semanticId of a              ❌     Uncheckable, semantic_id may not
            SubmodelElementCollection with             be resolvable

            SubmodelElementCollection/
            allowDuplicates == false

            references a ConceptDescription
            then the

            ConceptDescription/category
            shall be ENTITY.
AASd-093    If the semanticId of a              ❌     Uncheckable, semantic_id may not
            SubmodelElementCollection with             be resolvable

            SubmodelElementCollection/
            allowDuplicates == true

            references a ConceptDescription
            then the

            ConceptDescription/category shall
            be COLLECTION.
AASd-100    An attribute with data type         ✅
            "string"

            is not allowed to be empty
=========== =================================== ====== ===================================

