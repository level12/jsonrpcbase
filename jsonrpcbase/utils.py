import jsonschema
import json
import yaml
import os
from typing import Optional, Any, List

import jsonrpcbase.exceptions as exceptions


# Type of `obj` should be anything that has the __getitem__ method
def get_path(obj: Any, path: List[str]) -> Optional[Any]:
    """
    Get a nested value by a series of keys inside some nested indexable
    containers, returning None if the path does not exist, avoiding any errors.
    Args:
        obj: any indexable (has __getitem__ method) obj
        path: list of accessors, such as dict keys or list indexes
    Examples:
        get_path([{'x': {'y': 1}}], [0, 'x', 'y']) -> 1
    """
    for key in path:
        try:
            obj = obj[key]
        except Exception:
            return None
    return obj


def load_schema(path: str) -> dict:
    """
    Load, parse, and validate a JSON-Schema from a YAML or JSON file path.

    Args:
        path: file path to a JSON or YAML file
    Returns:
        An in-memory, jsonschema-validated python object

    throws InvalidSchemaError
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == '.yaml' or ext == '.yml':
        with open(path) as fd:
            schema = yaml.safe_load(fd)
    elif ext == '.json':
        with open(path) as fd:
            schema = json.load(fd)
    else:
        msg = f'Service schema must be YAML or JSON; {ext} is invalid'
        raise exceptions.InvalidSchemaError(msg)
    # Validate the schema
    jsonschema.Draft7Validator.check_schema(schema)
    if 'definitions' not in schema:
        msg = "No 'definitions' property found for the service schema"
        raise exceptions.InvalidSchemaError(msg)
    return schema
