# Copyright (c) 2025 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT
"""
This module provides the WSGI entry point for the Asset Administration Shell Repository Server.
"""

import logging
import os
from basyx.aas.adapter import load_directory
from basyx.aas.adapter.aasx import DictSupplementaryFileContainer
from basyx.aas.backend.local_file import LocalFileObjectStore
from basyx.aas.model.provider import DictObjectStore
from interfaces.repository import WSGIApp
from typing import Tuple


# -------- Helper methods --------

def setup_logger() -> logging.Logger:
    """
    Configure a custom :class:`~logging.Logger` for the start-up sequence of the server.

    :return: Configured :class:`~logging.Logger`
    """

    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(levelname)s [Server Start-up] %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def sync_input_to_storage(
        input_files: DictObjectStore,
        storage_files: LocalFileObjectStore,
        overwrite: bool
) -> Tuple[int, int, int]:
    """
    Merge :class:`Identifiables <basyx.aas.model.base.Identifiable>` from an in-memory
    :class:`~basyx.aas.model.provider.DictObjectStore` into a persistent
    :class:`~basyx.aas.backend.local_file.LocalFileObjectStore`.

    :param input_files: In-memory :class:`~basyx.aas.model.provider.DictObjectStore`
    :param storage_files: Persistent :class:`~basyx.aas.backend.local_file.LocalFileObjectStore`
    :param overwrite: Flag to overwrite existing :class:`Identifiables <basyx.aas.model.base.Identifiable>` in the
        :class:`~basyx.aas.backend.local_file.LocalFileObjectStore`
    :return: Counts of processed :class:`Identifiables <basyx.aas.model.base.Identifiable>` as
        ``(added, overwritten, skipped)``
    """

    added, overwritten, skipped = 0, 0, 0
    for identifiable in input_files:
        if identifiable.id in storage_files:
            if overwrite:
                existing = storage_files.get_identifiable(identifiable.id)
                storage_files.discard(existing)
                storage_files.add(identifiable)
                overwritten += 1
            else:
                skipped += 1
        else:
            storage_files.add(identifiable)
            added += 1
    return added, overwritten, skipped


def build_storage(
    env_input: str,
    env_storage: str,
    env_storage_persistency: bool,
    env_storage_overwrite: bool,
    logger: logging.Logger
) -> Tuple[DictObjectStore | LocalFileObjectStore, DictSupplementaryFileContainer]:
    """
    Configure the server's storage according to the given start-up settings.

    :param env_input: ``str`` pointing to the input directory of the server
    :param env_storage: ``str`` pointing to the :class:`~basyx.aas.backend.local_file.LocalFileObjectStore` storage
        directory of the server if persistent storage is enabled
    :param env_storage_persistency: Flag to enable persistent storage
    :param env_storage_overwrite: Flag to overwrite existing :class:`Identifiables <basyx.aas.model.base.Identifiable>`
        in the :class:`~basyx.aas.backend.local_file.LocalFileObjectStore` if persistent storage is enabled
    :param logger: :class:`~logging.Logger` used for start-up diagnostics
    :return: Tuple consisting of a :class:`~basyx.aas.model.provider.DictObjectStore` if persistent storage is disabled
        or a :class:`~basyx.aas.backend.local_file.LocalFileObjectStore` if persistent storage is enabled and a
        :class:`~basyx.aas.adapter.aasx.DictSupplementaryFileContainer` as storage for
        :class:`~interfaces.repository.WSGIApp`
    """

    if env_storage_persistency:
        storage_files = LocalFileObjectStore(env_storage)
        storage_files.check_directory(create=True)
        if os.path.isdir(env_input):
            input_files, input_supp_files = load_directory(env_input)
            added, overwritten, skipped = sync_input_to_storage(input_files, storage_files, env_storage_overwrite)
            logger.info(
                "Loaded %d identifiable(s) and %d supplementary file(s) from \"%s\"",
                len(input_files), len(input_supp_files), env_input
            )
            logger.info(
                "Synced INPUT to STORAGE with %d added and %d %s",
                added,
                overwritten if env_storage_overwrite else skipped,
                "overwritten" if env_storage_overwrite else "skipped"
            )
            return storage_files, input_supp_files
        else:
            logger.warning("INPUT directory \"%s\" not found, starting empty", env_input)
            return storage_files, DictSupplementaryFileContainer()

    if os.path.isdir(env_input):
        input_files, input_supp_files = load_directory(env_input)
        logger.info(
            "Loaded %d identifiable(s) and %d supplementary file(s) from \"%s\"",
            len(input_files), len(input_supp_files), env_input
        )
        return input_files, input_supp_files
    else:
        logger.warning("INPUT directory \"%s\" not found, starting empty", env_input)
        return DictObjectStore(), DictSupplementaryFileContainer()


# -------- WSGI entrypoint --------

logger = setup_logger()

env_input = os.getenv("INPUT", "/input")
env_storage = os.getenv("STORAGE", "/storage")
env_storage_persistency = os.getenv("STORAGE_PERSISTENCY", "false").lower() in {"1", "true", "yes"}
env_storage_overwrite = os.getenv("STORAGE_OVERWRITE", "false").lower() in {"1", "true", "yes"}
env_api_base_path = os.getenv("API_BASE_PATH")

wsgi_optparams = {"base_path": env_api_base_path} if env_api_base_path else {}

logger.info(
    "Loaded settings API_BASE_PATH=\"%s\", INPUT=\"%s\", STORAGE=\"%s\", PERSISTENCY=%s, OVERWRITE=%s",
    env_api_base_path or "", env_input, env_storage, env_storage_persistency, env_storage_overwrite
)

storage_files, supp_files = build_storage(
    env_input,
    env_storage,
    env_storage_persistency,
    env_storage_overwrite,
    logger
)

application = WSGIApp(storage_files, supp_files, **wsgi_optparams)


if __name__ == "__main__":
    logger.info("WSGI entrypoint created. Serve this module with uWSGI/Gunicorn/etc.")
