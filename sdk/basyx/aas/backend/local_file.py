# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module adds the functionality of storing and retrieving :class:`~basyx.aas.model.base.Identifiable` objects
in local files.

The :class:`~LocalFileIdentifiableStore` handles adding, deleting and otherwise managing
the AAS objects in a specific Directory.
"""
import contextlib
import hashlib
import json
import logging
import os
import tempfile
import threading
import warnings
import weakref
from pathlib import Path
from typing import Generator, Iterator, Optional, TextIO

from basyx.aas import model

from ..adapter.json import json_deserialization, json_serialization

try:
    import fcntl as _fcntl
except ImportError:
    _fcntl = None  # type: ignore  # Windows: directory locking is unavailable


logger = logging.getLogger(__name__)

class LockedDirectoryError(RuntimeError):
    pass


class DirectoryLock:
    """
    Implementation of a Lock on a directory. Uses POSIX ``flock`` on ``<directory>/.lock`` to control which instance
    holds the lock. Even if the process which holds the lock dies, the lock is released.

    The methods :meth:`acquire` and :meth:`release` are thread-safe and can be called in any state. If :meth:`acquire`
    is called when the directory is already locked no errors occur. The same holds for calling :meth:`release` in an
    unlocked state.

    .. note::
        Directory locking relies on ``fcntl.flock``, which is only available on POSIX platforms. On Windows
        acquiring a lock fails with a :class:`RuntimeError`. Override this behavior by setting parameter
        ``strict_locking`` to `False`.
    """

    def __init__(self, directory_path: str, strict_locking: bool = True):
        self.directory_path = Path(directory_path)
        self.lock_path = self.directory_path / ".lock"
        self._dir_lock_file: Optional[TextIO] = None
        self._strict_locking = strict_locking

        # We count the number of active accesses to the directory to ensure that
        # release() is only releasing if all are done
        self._locking_lock = threading.Condition()
        self._is_locked_flag = False
        self._active_accesses = 0
        self._is_releasing = False

    def acquire(self) -> None:
        """
        Acquires the lock on the directory non-blocking. If the ``<directory>/.lock`` file is already locked
        it raises a :class:`RuntimeError`.

        .. note::
            Directory locking relies on ``fcntl.flock``, which is only available on POSIX platforms. On Windows
            acquiring a lock fails with a :class:`RuntimeError`. Override this behavior by setting constructor
            parameter ``strict_locking`` to `False`.

        :raises RuntimeError: If the directory is already locked by another instance or fcntl is unavailable
        """
        with self._locking_lock:  # Ensure only one dir_lock is acquired at a time
            if self._is_locked_flag:
                return  # Idempotent

            self._dir_lock_file = open(self.lock_path, "a")  # use "a" to not swap the inode as in "w"

            if _fcntl is None:
                if self._strict_locking:
                    raise RuntimeError("fcntl unavailable, directory locking not possible."
                                        "Set strict_locking=False to continue unsafe operation on this system.")

                logger.warning("fcntl unavailable; directory locking is disabled (Windows?)")
                self._is_locked_flag = True
                return

            try:
                _fcntl.flock(self._dir_lock_file.fileno(), _fcntl.LOCK_EX | _fcntl.LOCK_NB)
            except BlockingIOError:
                # dir_lock already taken by other process
                self._dir_lock_file.close()
                self._dir_lock_file = None
                raise LockedDirectoryError(f"Directory {self.directory_path} "
                                           "is already locked by another DirectoryLock")
            else:
                self._is_locked_flag = True

    def release(self) -> None:
        """
        If the directory is currently locked, this method waits for all current accesses in :meth:`ensure_locked`
        to finish and releases the lock afterwards.
        """
        with self._locking_lock:
            if not self._is_locked_flag:
                return  # Idempotent
            self._is_releasing = True  # Restrict new ensure_locked() entries
            while self._active_accesses > 0:  # Wait for all active accesses to finish
                self._locking_lock.wait()

            # Release flock
            self._is_locked_flag = False
            self._is_releasing = False
            if self._dir_lock_file is not None:
                self._dir_lock_file.close()  # lock is released by closing fd
                self._dir_lock_file = None

    @contextlib.contextmanager
    def ensure_locked(self) -> Generator:
        """Context Manager for access to the locked directory

        Use this as a context manager when accessing files in the locked directory. This ensures that the directory
        is locked during the whole execution of the ``with`` block. Fails with a :class:`RuntimeError` if the directory
        is not locked when entering the ``with`` block.

        :raises RuntimeError: If the directory is not locked on enter
        """
        with self._locking_lock:
            if (not self._is_locked_flag) or self._is_releasing:
                raise RuntimeError(f"Directory {self.directory_path} is not locked!")
            self._active_accesses += 1
        try:
            yield
        finally:
            with self._locking_lock:
                self._active_accesses -= 1
                self._locking_lock.notify_all()

    def close(self) -> None:
        self.release()


class LocalFileIdentifiableStore(
    model.AbstractObjectStore[model.Identifier, model.Identifiable]
):
    """
    An ObjectStore implementation for :class:`~basyx.aas.model.base.Identifiable` BaSyx Python SDK objects backed
    by a local file based local backend.

    At most one instance of this class can manage a directory. To ensure this a
    :class:`~basyx.aas.backend.local_file.DirectoryLock` is used (with all it limitations on non-POSIX systems).
    The lock is applied eager (as soon as the directory exists) either in the constructor or after calling
    :meth:`check_directory`. Unless this is done all further method calls will fail with :class:`RuntimeError`.

    Call :meth:`close` to release the directory lock when done.

    .. warning::
        This backend is intended for development and testing only.
        Directory locking relies on ``fcntl.flock``, which is only available on POSIX platforms.
        On Windows system no concurrency control across processes is provided: concurrent writes to the same object
        (e.g. under a multi-worker WSGI server) will silently overwrite each other. Creating a store will result
        in a :class:`RuntimeError`.
        Use a dedicated database backend for any production deployment.
    """

    def __init__(self, directory_path: str, disable_strict_locking: bool = False):
        """
        Initializer of class LocalFileIdentifiableStore

        :param directory_path: Path to the local file backend (the path where you want to store your AAS JSON files).
        :param disable_strict_locking: Set to ``True`` to not fail on systems without fcntl (e.g. Windows). Warning:
                                        No concurrency control is provided!
        """
        self.directory_path: str = directory_path.rstrip("/")

        # A dictionary of weak references to local replications of stored objects. Objects are kept in this cache as
        # long as there is any other reference in the Python application to them. We use this to make sure that only one
        # local replication of each object is kept in the application and retrieving an object from the store always
        # returns the **same** (not only equal) object. Still, objects are forgotten, when they are not referenced
        # anywhere else to save memory.
        self._object_cache: weakref.WeakValueDictionary[
            model.Identifier, model.Identifiable
        ] = weakref.WeakValueDictionary()

        # Prevent concurrent write operations to avoid TOCTOU problems
        self._write_lock = threading.Lock()

        # We need to prevent multiple instances of LocalFileIdentifiableStore performing R/W operations on the same
        # directory in order to ensure cache validity. The directory is locked as soon as it exists.
        self._dir_lock = DirectoryLock(self.directory_path, strict_locking=not disable_strict_locking)
        if os.path.exists(self.directory_path):
            self._acquire_dir_lock()

    def _acquire_dir_lock(self) -> None:
        try:
            self._dir_lock.acquire()
        except LockedDirectoryError as ex:
            raise RuntimeError(f"Directory {self.directory_path} is already in use"
                               f" by another LocalFileIdentifiableStore instance.") from ex

    def close(self) -> None:
        """Release the directory lock. Call this when the store is no longer needed."""
        self._dir_lock.close()

    def check_directory(self, create=False):
        """
        Check if the directory exists and created it if not (and requested to do so)

        :param create: If True and the database does not exist, try to create it
        """
        if not os.path.exists(self.directory_path):
            if not create:
                raise FileNotFoundError(
                    "The given directory ({}) does not exist".format(
                        self.directory_path
                    )
                )
            # Create directory
            os.mkdir(self.directory_path)
            logger.info("Creating directory {}".format(self.directory_path))
        self._acquire_dir_lock()

    def get_identifiable_by_hash(self, hash_: str) -> model.Identifiable:
        """
        Retrieve an AAS object from the local file by its identifier hash

        :raises KeyError: If the respective file could not be found
        """
        with self._dir_lock.ensure_locked():
            try:
                with open("{}/{}.json".format(self.directory_path, hash_), "r") as file:
                    data = json.load(file, cls=json_deserialization.AASFromJsonDecoder)
                    obj = data["data"]
            except FileNotFoundError as e:
                raise KeyError(
                "No Identifiable with hash {} found in local file database".format(
                    hash_
                )
            ) from e
        with self._write_lock:
            if obj.id in self._object_cache:
                return self._object_cache[obj.id]
            self._object_cache[obj.id] = obj
        return obj

    def get_item(self, identifier: model.Identifier) -> model.Identifiable:
        """
        Retrieve an AAS object from the local file by its :class:`~basyx.aas.model.base.Identifier`

        :raises KeyError: If the respective file could not be found
        """
        with self._dir_lock.ensure_locked():
            with self._write_lock:
                if identifier in self._object_cache:
                    return self._object_cache[identifier]
            try:
                return self.get_identifiable_by_hash(self._transform_id(identifier))
            except KeyError as e:
                raise KeyError(
                "No Identifiable with id {} found in local file database".format(
                    identifier
                )
            ) from e

    def _write_atomic(self, x: model.Identifiable) -> None:
        """
        Serialize x to a temp file in the store directory, then atomically replace the final file.

        Using os.replace() (rename(2) on POSIX) ensures readers always see a complete file — never
        a partially-written one from a crash or concurrent access mid-write.
        """
        final_path = "{}/{}.json".format(self.directory_path, self._transform_id(x.id))
        tmp_fd, tmp_path = tempfile.mkstemp(dir=self.directory_path, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w") as tmp_file:
                json.dump(
                    {"data": x},
                    tmp_file,
                    cls=json_serialization.AASToJsonEncoder,
                    indent=4,
                )
            os.replace(tmp_path, final_path)
        # Catch all `Exception`s, as well as `KeyboardInterrupt` and `SystemExit` too, so the temp
        # file is never left behind even if the process is being torn down:
        except BaseException:
            os.unlink(tmp_path)
            raise

    def add(self, x: model.Identifiable) -> None:
        """
        Add an object to the store

        :raises KeyError: If an object with the same id exists already in the object store
        """
        logger.debug("Adding object %s to Local File Store ...", repr(x))
        with self._write_lock:
            with self._dir_lock.ensure_locked():
                if os.path.exists(
                    "{}/{}.json".format(self.directory_path, self._transform_id(x.id))
                ):
                    raise KeyError(
                        "Identifiable with id {} already exists in local file database".format(
                            x.id
                        )
                    )
                self._write_atomic(x)

            self._object_cache[x.id] = x

    def commit(self, x: model.Identifiable) -> None:
        """
        Write the current in-memory state of a stored object back to its file.

        :param x: The object to persist
        :raises KeyError: If the object is not present in the store
        """
        with self._write_lock:
            with self._dir_lock.ensure_locked():
                if not os.path.exists(
                    "{}/{}.json".format(self.directory_path, self._transform_id(x.id))
                ):
                    raise KeyError(
                "No AAS object with id {} exists in local file database".format(x.id)
            )
                self._write_atomic(x)

    def discard(self, x: model.Identifiable) -> None:
        """
        Delete an :class:`~basyx.aas.model.base.Identifiable` AAS object from the local file store

        :param x: The object to be deleted
        :raises KeyError: If the object does not exist in the database
        """
        logger.debug("Deleting object %s from Local File Store database ...", repr(x))
        with self._write_lock:
            with self._dir_lock.ensure_locked():
                try:
                    os.remove(
                        "{}/{}.json".format(self.directory_path, self._transform_id(x.id))
                    )
                except FileNotFoundError as e:
                    raise KeyError(
                        "No AAS object with id {} exists in local file database".format(x.id)
                    ) from e

            self._object_cache.pop(x.id, None)

    def __contains__(self, x: object) -> bool:
        """
        Check if an object with the given :class:`~basyx.aas.model.base.Identifier` or the same
        :class:`~basyx.aas.model.base.Identifier` as the given object is contained in the local file database

        :param x: AAS object :class:`~basyx.aas.model.base.Identifier` or :class:`~basyx.aas.model.base.Identifiable`
                  AAS object
        :return: ``True`` if such an object exists in the database, ``False`` otherwise
        """
        if isinstance(x, model.Identifier):
            identifier = x
        elif isinstance(x, model.Identifiable):
            identifier = x.id
        else:
            return False
        logger.debug("Checking existence of object with id %s in database ...", repr(x))
        with self._dir_lock.ensure_locked():
            return os.path.exists(
                "{}/{}.json".format(self.directory_path, self._transform_id(identifier))
            )

    def __len__(self) -> int:
        """
        Retrieve the number of objects in the local file database

        :return: The number of objects (determined from the number of documents)
        """
        logger.debug("Fetching number of documents from database ...")
        with self._dir_lock.ensure_locked():
            return sum(
                1 for f in os.listdir(self.directory_path) if f.lower().endswith(".json")
            )

    def __iter__(self) -> Iterator[model.Identifiable]:
        """
        Iterate all :class:`~basyx.aas.model.base.Identifiable` objects in the CouchDB database.

        This method returns an iterator, containing only a list of all identifiers in the database and retrieving
        the identifiable objects on the fly.
        """
        logger.debug("Iterating over objects in database ...")
        with self._dir_lock.ensure_locked():
            for name in os.listdir(self.directory_path):
                if name.lower().endswith(".json"):
                    yield self.get_identifiable_by_hash(name[:-5])

    @staticmethod
    def _transform_id(identifier: model.Identifier) -> str:
        """
        Helper method to represent an ASS Identifier as a string to be used as Local file document id
        """
        return hashlib.sha256(identifier.encode("utf-8")).hexdigest()


class LocalFileObjectStore(LocalFileIdentifiableStore):
    """
    `LocalFileObjectStore` has been renamed to :class:`~.LocalFileIdentifiableStore` and will be removed in a
    future release. Please migrate to :class:`~.LocalFileIdentifiableStore`.
    """

    def __init__(self, directory_path: str):
        warnings.warn(
            "`LocalFileObjectStore` is deprecated and will be removed in a future release. Use "
            "`LocalFileIdentifiableStore` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(directory_path)

    def get_identifiable(self, identifier: model.Identifier) -> model.Identifiable:
        warnings.warn(
            "`get_identifiable()` is deprecated. Use `get_item()` from `LocalFileIdentifiableStore` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().get_item(identifier)
