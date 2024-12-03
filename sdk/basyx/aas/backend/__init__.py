"""
This module implements a standardized way of integrating data from existing systems into AAS objects. To achieve this,
the abstract :class:`~basyx.aas.backend.backends.Backend` class implements the class methods
:meth:`~basyx.aas.backend.backends.Backend.update_object` and :meth:`~basyx.aas.backend.backends.Backend.commit_object`,
which every implementation of a backend needs to overwrite. For a tutorial on how to implement a backend, see
:ref:`this tutorial <tutorial_backend_couchdb>`
"""
