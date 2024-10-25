#!/usr/bin/env python3
# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for storing Asset Administration Shells, Submodels and Assets in a CouchDB database server, using the
CouchDBObjectStore and CouchDB Backend.

This tutorial also shows the usage of the commit()/update() mechanism for synchronizing objects with an external data
source.
"""

from configparser import ConfigParser
from pathlib import Path

import basyx.aas.examples.data.example_aas
import basyx.aas.backend.couchdb

# To execute this tutorial, you'll need a running CouchDB server, including an empty database and a user account with
# access to that database.
# After installing CouchDB, you can use the CouchDB web interface "Fauxton" (typically at
# http://localhost:5984/_utils/) to create a new database. Optionally, you can create a new user by adding a document
# to the `_users` database with the following contents (notice that the username is required in two positions):
#
#     {"_id": "org.couchdb.user:<your username>",
#      "name": "<your username>",
#      "password": "<your password>",
#      "roles": [],
#      "type": "user"}
#
# Afterwards you can add the new user to the set of "Members" of your new database (via the "Permissions" section in the
# user interface). Alternatively, you can use the admin credentials with the BaSyx Python SDK (see below).

# Step-by-Step Guide:
# step 1: connecting to a CouchDB server
# step 2: storing objects in CouchDBObjectStore
# step 3: updating objects from the CouchDB and committing changes


##########################################
# Step 1: Connecting to a CouchDB Server #
##########################################

# Well, actually, connections to the CouchDB server are created by the CouchDB backend, as required. However, we need
# to provide the login credentials to the server for this to work.
#
# Here, we take the test configuration to work with BaSyx development environments. You should replace these with
# the url of your CouchDB server (typically http://localhost:5984), the name of the empty database, and the name and
# password of a CouchDB user account which is "member" of this database (see above). Alternatively, you can provide
# your CouchDB server's admin credentials.
config = ConfigParser()
config.read([Path(__file__).parent.parent.parent.parent / 'test' / 'test_config.default.ini',
             Path(__file__).parent.parent.parent.parent / 'test' / 'test_config.ini'])

couchdb_url = config['couchdb']['url']
couchdb_database = config['couchdb']['database']
couchdb_user = config['couchdb']['user']
couchdb_password = config['couchdb']['password']


# Provide the login credentials to the CouchDB backend.
# These credentials are used whenever communication with this CouchDB server is required either via the
# CouchDBObjectStore or via the update()/commit() backend.
basyx.aas.backend.couchdb.register_credentials(couchdb_url, couchdb_user, couchdb_password)

# Now, we create a CouchDBObjectStore as an interface for managing the objects in the CouchDB server.
object_store = basyx.aas.backend.couchdb.CouchDBObjectStore(couchdb_url, couchdb_database)


#####################################################
# Step 2: Storing objects in the CouchDBObjectStore #
#####################################################

# Create some example objects
example_submodel1 = basyx.aas.examples.data.example_aas.create_example_asset_identification_submodel()
example_submodel2 = basyx.aas.examples.data.example_aas.create_example_bill_of_material_submodel()

# The CouchDBObjectStore behaves just like other ObjectStore implementations (see `tutorial_storage.py`). The objects
# are transferred to the CouchDB immediately. Additionally, the `source` attribute is set automatically, so update() and
# commit() will work automatically (see below).
object_store.add(example_submodel1)
object_store.add(example_submodel2)


####################################################################
# Step 3: Updating Objects from the CouchDB and Committing Changes #
####################################################################

# Since the CouchDBObjectStore has set the `source` attribute of our Submodel objects, we can now use update() and
# commit() to synchronize changes to these objects with the database. The `source` indicates (via its URI scheme) that
# the CouchDB backend is used for the synchronization and references the correct CouchDB server url and database. For
# this to work, we must make sure to `import aas.backend.couchdb` at least once in this Python application, so the
# CouchDB backend is loaded.

# Fetch recent updates from the server
example_submodel1.update()

# Make some changes to a Property within the submodel
prop = example_submodel1.get_referable('ManufacturerName')
assert isinstance(prop, basyx.aas.model.Property)

prop.value = "RWTH Aachen"

# Commit (upload) these changes to the CouchDB server
# We can simply call commit() on the Property object. It will check the `source` attribute of the object itself as well
# as the source attribute of all ancestors in the object hierarchy (including the Submodel) and commit the changes to
# all of these external data sources.
prop.commit()


############
# Clean up #
############

# Let's delete the Submodels from the CouchDB to leave it in a clean state
object_store.discard(example_submodel1)
object_store.discard(example_submodel2)
