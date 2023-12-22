base - Abstract Classes and Basic Structures
============================================

.. automodule:: basyx.aas.model.base
    :exclude-members: ConstrainedList, LangStringSet

    .. autoclass:: ConstrainedList
          :exclude-members: clear

    .. autoclass:: LangStringSet
          :exclude-members: clear


Constrained String Datatypes
----------------------------

These types are aliases of :class:`str` and constrained by a setter where used.

.. autoclass:: ContentType
.. autoclass:: Identifier
.. autoclass:: LabelType
.. autoclass:: MessageTopicType
.. autoclass:: NameType
.. autoclass:: PathType
.. autoclass:: QualifierType
.. autoclass:: RevisionType
.. autoclass:: ShortNameType
.. autoclass:: VersionType
.. autoclass:: ValueTypeIEC61360


Type Aliases
------------
.. autoclass:: DataTypeDefXsd
.. autoclass:: ValueDataType
.. autoclass:: ValueList
.. autoclass:: BlobType


Type Variables
--------------
.. autoclass:: _NSO
.. autoclass:: _RT
.. autoclass:: _T
