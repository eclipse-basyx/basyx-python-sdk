from typing import Literal, Type, Optional
import logging

def create_mock_effect(
        module: str,
        level: Literal['error', 'warning', 'info', 'debug'],
        error_cls: Type[Exception] = ValueError,
        error_msg: Optional[str] = None
):
    error_msg = error_msg or f"Test {level}!"

    def mock_error(*args, **kwargs):
        if kwargs.get('failsafe', True):
            getattr(logging.getLogger(module), level)(error_msg)
        else:
            raise error_cls(error_msg)

    return mock_error

