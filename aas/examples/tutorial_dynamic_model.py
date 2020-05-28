#!/usr/bin/env python3
# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for the creation of a SubmodelElementCollection of Properties, which are dynamically updated from a proprietary
data source. As an example, this tutorial uses the `psutil` library to represent the local computer's process list.
"""
import datetime
from typing import List

import psutil  # type: ignore

from aas import model
from aas.adapter.json import write_aas_json_file

# This tutorial shows how SubmodelElements can be customized to dynamically reflect values from a proprietary data
# source. The presented method can be used to create dynamic submodels, representing an SQL database's data or values
# of local variables within the Asset Administration Shell data model. These submodels can be serialized to create
# an AAS-compliant snapshot of the current data or be attached to the HTTP server for reading (and even modifying) the
# values via the AAS API.
#
# The basic idea is to create custom subclasses of PyI40AAS's model classes, which are bound to the specific data source
# and fetch the current values dynamically from that data source. For this purpose, the `update()` and `commit()`
# methods are overridden, which should be called by any code using the AAS model objects (including the HTTP server) to
# values should be synchronized from or to underlying data sources.
#
# In this tutorial, we use the `psutil` library to create a SubmodelElementCollection of all processes running on the
# local computer, containing a SubmodelElementCollection for each process, which contain three Properties each: the
# process id, the process name and the current memory usage of the process. (Providing CPU utilization values would be
# a bit harder, since it needs to be measured over a period of time.)


##############################################################################################################
# Step 1: create custom Property and SubmodelElementCollection classes to hold a process's memory usage, all #
#         properties of a single process and a list of all processes.                                        #
##############################################################################################################

class ProcessMemProperty(model.Property):
    """
    A special Property class to represent a system process's memory usage

    It inherits from the normal `model.Propery` class, but overrides the `__init__()` method, as well as the `update()`
    method. Each instance of such a Property is bound to a specific process. The new `update()` method updates the
    object's `value` attribute with the current memory usage of that process. For this purpose, it holds a reference to
    psutil's `Process` object representing the process.
    """
    def __init__(self, process: psutil.Process, id_short: str):
        super().__init__(id_short, model.datatypes.Float, None)
        self.process = process
        self.last_update: datetime.datetime = datetime.datetime.fromtimestamp(0)

    def update(self, timeout: float = 0) -> None:
        if datetime.datetime.now() - self.last_update < datetime.timedelta(seconds=timeout):
            return
        try:
            self.value = self.process.memory_percent()
        except psutil.Error:
            # Set value to None in case of an error while fetching the memory usage
            self.value = None
        self.last_update = datetime.datetime.now()

    def commit(self) -> None:
        raise AttributeError("A process's memory usage is a read-only property.")


class ProcessDataCollection(model.SubmodelElementCollectionUnordered):
    """
    This class is a special SubmodelElementCollection to hold all properties of a single process.

    It inherits from the normal `model.SubmodelElementCollection` class. In addition to the usual attributes, it defines
    a new instance attribute `pid`, which holds the process id of the represented process. The new `__init__()` method
    retrieves the static attributes of the process using `psutil` and creates all the Properties to represent the
    process with well-known idShort values:

    * pid -- A static int-Property containing the process id
    * name -- A static string-Property containing the process name (executable name)
    * mem -- A dynamic float-Property representing the current memory usage of the process in percent. Uses the custom
      `ProcessMemProperty` class
    """
    def __init__(self, pid: int, id_short: str):
        super().__init__(id_short)
        self.pid = pid
        process = psutil.Process(pid)

        self.value.add(model.Property("pid", model.datatypes.Integer, pid))
        self.value.add(model.Property("name", model.datatypes.String, process.name()))
        self.value.add(ProcessMemProperty(process, "mem"))

    def update(self, timeout: float = 0) -> None:
        # Only the 'mem' Property needs to be updated dynamically. The other Properties are static.
        self.get_referable('mem').update(timeout)

    def commit(self) -> None:
        raise AttributeError("A process is a read-only property collection.")


class ProcessList(model.SubmodelElementCollectionUnordered):
    """
    A special SubmodelElementCollection, representing a (dynamically updated) list of all processes on the local system

    It inherits from the normal `model.SubmodelElementCollection` class and amends it with a more sophisticated
    `update()` method to update the list of contained elements based on the current process list of the computer.
    """
    def __init__(self, id_short: str):
        super().__init__(id_short)

    def update(self, timeout: float = 0) -> None:
        # Get the current list of running processes' ids
        pids = psutil.pids()

        # 1. Step: Delete old ProcessDataCollections
        # Attention: We must not modify the NamespaceSet in `self.value` while iterating over it. Thus, we first create
        # a list of the children to be deleted and delete them in a second run.
        children_to_remove: List[model.SubmodelElement] = [c
                                                           for c in self.value
                                                           if (not isinstance(c, ProcessDataCollection)
                                                               or c.pid not in pids)]
        for c in children_to_remove:
            self.value.discard(c)

        # 2. Step: Add ProcessDataCollections for new processes
        # We use the process id (pid) as idShort, so we can easily check if the ProcessDataCollection exists already
        for pid in pids:
            id_short = "process_{}".format(pid)
            if id_short not in self.value:  # The NamespaceSet object in `self.value` allows for a given id_short
                try:
                    self.value.add(ProcessDataCollection(pid, id_short))
                except psutil.AccessDenied:
                    # Skip process in case we are not allowed to access its details
                    pass

        # 3. Step: Update the data within the ProcessDataCollections recursively
        for c in self.value:
            c.update()

    def commit(self) -> None:
        raise AttributeError("A process list is a read-only collection.")


###########################################################
# Step 2: Use an instance of the custom ProcessList class #
###########################################################

# Create a Submodel including a ProcessList instance
submodel = model.Submodel(
    identification=model.Identifier('https://acplt.org/ComputerInformationTest', model.IdentifierType.IRI),
    submodel_element={ProcessList('processes')}
)

# Update the complete process list to have current data
# TODO in future it will be sufficient to `update()` the submodel, which should propagate the request recursively.
submodel.get_referable('processes').update()

# Write the submodel to a JSON file.
# See `tutorial_serialization_deserialization_json.py` for more information.
obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
obj_store.add(submodel)
with open('ComputerInformationTest.json', 'w') as f:
    write_aas_json_file(f, obj_store, indent=4)
