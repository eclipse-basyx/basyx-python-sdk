#!/usr/bin/env python3
# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for exporting Asset Administration Shells with related objects and auxiliary files to AASX package files, using
the aas.adapter.aasx module from PyI40AAS.

.. warning:
    This tutorial is only valid for the 0.2.x branch of PyI40AAS. With version 3.0 of *Details of the Asset
    Administration Shell* (i.e. version 0.3.x of PyI40AAS) some specifications of AASX files will change, resulting in
    changes of the `AASXWriter` interface.
"""
import datetime
from pathlib import Path  # Used for easier handling of auxiliary file's local path

import pyecma376_2  # The base library for Open Packaging Specifications. We will use the OPCCoreProperties class.
from aas import model
from aas.adapter import aasx

# step 1: Setting up an SupplementaryFileContainer and AAS & submodel with File objects
# step 2: Writing AAS objects and auxiliary files to an AASX package
# step 3: Reading AAS objects and auxiliary files from an AASX package


#########################################################################################
# Step 1: Setting up an SupplementaryFileContainer and AAS & submodel with File objects #
#########################################################################################

# Let's first create a basic Asset Adminstration Shell with a simple submodel.
# See `tutorial_create_simple_aas.py` for more details.

submodel = model.Submodel(
    identification=model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI)
)
asset = model.Asset(
    kind=model.AssetKind.INSTANCE,  # define that the Asset is of kind instance
    identification=model.Identifier(id_='https://acplt.org/Simple_Asset', id_type=model.IdentifierType.IRI)
)
aas = model.AssetAdministrationShell(
    identification=model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI),
    asset=model.AASReference.from_referable(asset),
    submodel={model.AASReference.from_referable(submodel)}
)

# Another submodel, which is not related to the AAS:
unrelated_submodel = model.Submodel(
    identification=model.Identifier('https://acplt.org/Unrelated_Submodel', model.IdentifierType.IRI)
)

# We add these objects to an ObjectStore for easy retrieval by identification.
# See `tutorial_storage.py` for more details. We could also use a database-backed ObjectStore here
# (see `tutorial_backend_couchdb.py`).
object_store = model.DictObjectStore([submodel, asset, aas, unrelated_submodel])


# For holding auxiliary files, which will eventually be added to an AASX package, we need an SupplementaryFileContainer.
# The `DictSupplementaryFileContainer` is a simple SupplementaryFileContainer, that stores the files' contents in simple
# bytes objects in memory.
file_store = aasx.DictSupplementaryFileContainer()

# Now, we add an example file from our local filesystem to the SupplementaryFileContainer.
#
# For this purpose, we need to specify the file's name in the SupplementaryFileContainer. This name is used to reference
# the file in the container and will later be used as the filename in the AASX package file. Thus, this file must begin
# with a slash and should begin with `/aasx/`. Here, we use `/aasx/suppl/MyExampleFile.pdf`. The
# SupplementaryFileContainer's add_file() method will ensure uniqueness of the name by adding a suffix if a equally
# named file with different contents exists. The final name is returned.
#
# In addition, we need to specify the MIME type of the file, which is later used in the metadata of the AASX package.
# (This is actually a )

with open(Path(__file__).parent / 'data' / 'TestFile.pdf', 'rb') as f:
    actual_file_name = file_store.add_file("/aasx/suppl/MyExampleFile.pdf", f, "application/pdf")


# With the actual_file_name in the SupplementaryFileContainer, we can create a reference to that file in our AAS
# Submodel, in the form of a `File` object:

submodel.submodel_element.add(
    model.File(id_short="documentationFile",
               mime_type="application/pdf",
               value=actual_file_name))


######################################################################
# Step 2: Writing AAS objects and auxiliary files to an AASX package #
######################################################################

# After setting everything up in Step 1, writing the AAS, including the Submdel and Asset objects and the auxiliary
# file to an AASX package is simple.

# Open an AASXWriter with the destination file name and use it as a context handler, to make sure it is properly closed
# after doing the modifications:
with aasx.AASXWriter("MyAASXPackage.aasx") as writer:
    # Write the AAS and everything belonging to it to the AASX package
    # The `write_aas()` method will automatically fetch the AAS object with the given identification, the referenced
    # Asset object and all referenced Submodel and ConceptDescription objects from the ObjectStore. It will also
    # scan all sbmodels for `File` objects and fetch the referenced auxiliary files from the SupplementaryFileContainer.
    writer.write_aas(aas_id=model.Identifier('https://acplt.org/Simple_AAS', model.IdentifierType.IRI),
                     object_store=object_store,
                     file_store=file_store,
                     submodel_split_parts=False)  # for compatibility with AASX Package Explorer

    # For adding a second AAS to the package, we can simply call `write_aas()` again.
    # Warning: This will create a second XML/JSON part in the AASX Package, which is compliant with the "Details of the
    # Asset Administration Shell" standard up to version 2.0.1, but not supported by AASX Package Explorer.

    # We can also use a more low-level interface to add a JSON/XML part with any Identifiable objects (not only an AAS
    # and referenced objects) in the AASX package manually. `write_aas_objects()` will also take care of adding
    # referenced auxiliary files by scanning all submodel objects for contained `File` objects.
    # Warning: AASX Package Explorer will only read the first XML part in an AASX package. Thus, in this example, it
    # will only find the objects, written by `write_aas()` above.
    writer.write_aas_objects(part_name="/aasx/my_aas_part.xml",
                             object_ids=[
                                 model.Identifier('https://acplt.org/Unrelated_Submodel', model.IdentifierType.IRI)
                                 ],
                             object_store=object_store,
                             file_store=file_store)

    # We can also add a thumbnail image to the package (using `writer.write_thumbnail()`) or add metadata:
    meta_data = pyecma376_2.OPCCoreProperties()
    meta_data.creator = "Chair of Process Control Engineering"
    meta_data.created = datetime.datetime.now()
    writer.write_core_properties(meta_data)

# Closing the AASXWriter will write some required parts with relationships and MIME types to the AASX package file and
# close the package file afterwards. Make sure, to always call `AASXWriter.close()` or use the AASXWriter in a `with`
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
    # In contrast to the AASX Package Explorer, we are not limited to a single XML part in the package, but instead we
    # will read the contents of all included JSON and XML parts into the ObjectStore
    reader.read_into(object_store=new_object_store,
                     file_store=new_file_store)

    # We can also read the meta data
    new_meta_data = reader.get_core_properties()

    # We could also read the thumbnail image, using `reader.get_thumbnail()`


# Some quick checks to make sure, reading worked as expected
assert model.Identifier('https://acplt.org/Simple_Submodel', model.IdentifierType.IRI) in new_object_store
assert model.Identifier('https://acplt.org/Unrelated_Submodel', model.IdentifierType.IRI) in new_object_store
assert actual_file_name in new_file_store
assert new_meta_data.creator == "Chair of Process Control Engineering"
