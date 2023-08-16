"""Shared utilities for pytest."""
import json
import tempfile
from typing import Any, Dict

import pytest


@pytest.fixture(scope="function")
def json_file():
    """Create a json file from a python object."""
    with tempfile.NamedTemporaryFile("r", suffix=".json", delete=False) as file:

        def create_file(model: Dict[str, Any]):
            with open(file.name, "w") as fp:
                json.dump(model, fp)
            return file

        yield create_file
        file.delete = True
        file.close()
