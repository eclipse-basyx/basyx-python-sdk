import datetime
import io
import logging
from typing import Literal, Optional, Type

import pyecma376_2
from basyx.aas.examples.data import TEST_PDF_FILE, create_example_aas_binding


def create_example_aas_core_properties() -> pyecma376_2.OPCCoreProperties:
    """Create core properties similar to the example AASX file."""

    cp = pyecma376_2.OPCCoreProperties()
    cp.created = datetime.datetime(2020, 1, 1, 0, 0, 0)
    cp.creator = "Eclipse BaSyx Python Testing Framework"
    cp.description = "Test_Description"
    cp.lastModifiedBy = "Eclipse BaSyx Python Testing Framework Compliance Tool"
    cp.modified = datetime.datetime(2020, 1, 1, 0, 0, 1)
    cp.revision = "1.0"
    cp.version = "2.0.1"
    cp.title = "Test Title"
    return cp


def create_read_into_mock(file: Literal['TestFile', 'TestFileWrong', None]):
    """"Creates side effect function for the AASXReader.read_into mock"""

    def fill_stores(store, file_store, **kwargs) -> None:
        for item in create_example_aas_binding():
            store.add(item)

        if file == 'TestFile':
            with open(TEST_PDF_FILE, 'rb') as f:
                file_store.add_file("/TestFile.pdf", f, "application/pdf")
        elif file == 'TestFileWrong':
            file_store.add_file("/TestFile.pdf", io.BytesIO(b"dummy"), "application/pdf")
    return fill_stores


def create_mock_effect(
        module: str,
        level: Literal['error', 'warning', 'info', 'debug'],
        error_cls: Type[Exception] = ValueError,
        error_msg: Optional[str] = None
):
    """Create mock function, that raises or logs error (based on `failsafe` argument)"""

    error_msg = error_msg or f"Test {level}!"

    def mock_error(*args, **kwargs):
        if kwargs.get('failsafe', True):
            getattr(logging.getLogger(module), level)(error_msg)
        else:
            raise error_cls(error_msg)

    return mock_error
