"""
.. _adapter.rdf.__init__:

This package contains functionality for serialization and deserialization of BaSyx Python SDK objects into RDF.

:ref:`rdf_serialization <adapter.xml.rdf_serialization>`: The module offers a function to write an
:class:`ObjectStore <basyx.aas.model.provider.AbstractObjectStore>` to a given file.
"""

from .rdf_serialization import AASToRDFEncoder, object_store_to_rdf, write_aas_rdf_file
