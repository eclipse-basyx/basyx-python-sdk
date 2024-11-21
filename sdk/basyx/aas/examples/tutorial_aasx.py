#!/usr/bin/env python3
# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for exporting Asset Administration Shells with related objects and auxiliary files to AASX package files, using
the :mod:`~basyx.aas.adapter.aasx` module from the Eclipse BaSyx Python SDK.

.. warning::
    This tutorial is only valid for the current main branch of the Eclipse BaSyx Python SDK. With version 3.0 of
    *Details of the Asset Administration Shell* some specifications of AASX files will change, resulting in changes of
    the :class:`~basyx.aas.adapter.aasx.AASXWriter` interface.
"""
import datetime
from pathlib import Path  # Used for easier handling of auxiliary file's local path

import pyecma376_2  # The base library for Open Packaging Specifications. We will use the OPCCoreProperties class.
from basyx.aas import model
from basyx.aas.adapter import aasx

# step 1: Setting up an SupplementaryFileContainer and AAS & submodel with File objects
# step 2: Writing AAS objects and auxiliary files to an AASX package
# step 3: Reading AAS objects and auxiliary files from an AASX package


########################################################################################
# Step 1: Setting up a SupplementaryFileContainer and AAS & submodel with File objects #
########################################################################################

# Let's first create a basic Asset Administration Shell with a simple submodel.
# See `tutorial_create_simple_aas.py` for more details.

submodel = model.Submodel(
    id_='https://acplt.org/Simple_Submodel'
)
aas = model.AssetAdministrationShell(
    id_='https://acplt.org/Simple_AAS',
    asset_information=model.AssetInformation(
        asset_kind=model.AssetKind.INSTANCE,
        global_asset_id='http://acplt.org/Simple_Asset'
    ),
    submodel={model.ModelReference.from_referable(submodel)}
)

# Another submodel, which is not related to the AAS:
unrelated_submodel = model.Submodel(
    id_='https://acplt.org/Unrelated_Submodel'
)

# We add these objects to an ObjectStore for easy retrieval by id.
# See `tutorial_storage.py` for more details. We could also use a database-backed ObjectStore here
# (see `tutorial_backend_couchdb.py`).
object_store = model.DictObjectStore([submodel, aas, unrelated_submodel])


# For holding auxiliary files, which will eventually be added to an AASX package, we need a SupplementaryFileContainer.
# The `DictSupplementaryFileContainer` is a simple SupplementaryFileContainer that stores the files' contents in simple
# bytes objects in memory.
file_store = aasx.DictSupplementaryFileContainer()

# Now, we add an example file from our local filesystem to the SupplementaryFileContainer.
#
# For this purpose, we need to specify the file's name in the SupplementaryFileContainer. This name is used to reference
# the file in the container and will later be used as the filename in the AASX package file. Thus, this file must begin
# with a slash and should begin with `/aasx/`. Here, we use `/aasx/suppl/MyExampleFile.pdf`. The
# SupplementaryFileContainer's add_file() method will ensure uniqueness of the name by adding a suffix if an equally
# named file with different contents exists. The final name is returned.
#
# In addition, we need to specify the MIME type of the file, which is later used in the metadata of the AASX package.
# (This is actually a requirement of the underlying Open Packaging Conventions (ECMA376-2) format, which imposes the
# specification of the MIME type ("content type") of every single file within the package.)

with open(Path(__file__).parent / 'data' / 'TestFile.pdf', 'rb') as f:
    actual_file_name = file_store.add_file("/aasx/suppl/MyExampleFile.pdf", f, "application/pdf")


# With the actual_file_name in the SupplementaryFileContainer, we can create a reference to that file in our AAS
# Submodel, in the form of a `File` object:

submodel.submodel_element.add(
    model.File(id_short="documentationFile",
               content_type="application/pdf",
               value=actual_file_name))


######################################################################
# Step 2: Writing AAS objects and auxiliary files to an AASX package #
######################################################################

# After setting everything up in Step 1, writing the AAS, including the Submodel objects and the auxiliary file
# to an AASX package is simple.

# Open an AASXWriter with the destination file name and use it as a context handler, to make sure it is properly closed
# after doing the modifications:
with aasx.AASXWriter("MyAASXPackage.aasx") as writer:
    # Write the AAS and everything belonging to it to the AASX package
    # The `write_aas()` method will automatically fetch the AAS object with the given id
    # and all referenced Submodel objects from the ObjectStore. It will also scan every object for
    # semanticIds referencing ConceptDescription, fetch them from the ObjectStore, and scan all submodels for `File`
    # objects and fetch the referenced auxiliary files from the SupplementaryFileContainer.
    # In order to add more than one AAS to the package, we can simply add more Identifiers to the `aas_ids` list.
    #
    # ATTENTION: As of Version 3.0 RC01 of Details of the Asset Administration Shell, it is no longer valid to add more
    # than one "aas-spec" part (JSON/XML part with AAS objects) to an AASX package. Thus, `write_aas` MUST
    # only be called once per AASX package!
    writer.write_aas(aas_ids=['https://acplt.org/Simple_AAS'],
                     object_store=object_store,
                     file_store=file_store)

    # Alternatively, we can use a more low-level interface to add a JSON/XML part with any Identifiable objects (not
    # only an AAS and referenced objects) in the AASX package manually. `write_aas_objects()` will also take care of
    # adding referenced auxiliary files by scanning all submodel objects for contained `File` objects.
    #
    # ATTENTION: As of Version 3.0 RC01 of Details of the Asset Administration Shell, it is no longer valid to add more
    # than one "aas-spec" part (JSON/XML part with AAS objects) to an AASX package. Thus, `write_all_aas_objects` SHALL
    # only be used as an alternative to `write_aas` and SHALL only be called once!
    objects_to_be_written: model.DictObjectStore[model.Identifiable] = model.DictObjectStore([unrelated_submodel])
    writer.write_all_aas_objects(part_name="/aasx/my_aas_part.xml",
                                 objects=objects_to_be_written,
                                 file_store=file_store)

    # We can also add a thumbnail image to the package (using `writer.write_thumbnail()`) or add metadata:
    meta_data = pyecma376_2.OPCCoreProperties()
    meta_data.creator = "Chair of Process Control Engineering"
    meta_data.created = datetime.datetime.now()
    writer.write_core_properties(meta_data)

# Closing the AASXWriter will write some required parts with relationships and MIME types to the AASX package file and
# close the package file afterward. Make sure, to always call `AASXWriter.close()` or use the AASXWriter in a `with`
# statement (as a context manager) as shown above.


########################################################################
# Step 3: Reading AAS objects and auxiliary files from an AASX package #
########################################################################

# Let's read the AASX package file, we have just written.
# We'll use a fresh ObjectStore and SupplementaryFileContainer to read AAS objects and auxiliary files into.
new_object_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
new_file_store = aasx.DictSupplementaryFileContainer()

# Again, we need to use the AASXReader as a context manager (or call `.close()` in the end) to make sure the AASX
# package file is properly closed when we are finished.
with aasx.AASXReader("MyAASXPackage.aasx") as reader:
    # Read all contained AAS objects and all referenced auxiliary files
    reader.read_into(object_store=new_object_store,
                     file_store=new_file_store)

    # We can also read the metadata
    new_meta_data = reader.get_core_properties()

    # We could also read the thumbnail image, using `reader.get_thumbnail()`


# Some quick checks to make sure, reading worked as expected
assert 'https://acplt.org/Simple_Submodel' in new_object_store
assert actual_file_name in new_file_store
assert new_meta_data.creator == "Chair of Process Control Engineering"
