"""
Simple JSON-RPC service without transport layer

See README.md for details

Uses Google Style Python docstrings:
    https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
"""
import json
import logging
import jsonschema
from typing import Callable, Optional, List, Union

import jsonrpcbase.exceptions as exceptions

# Reference: https://www.jsonrpc.org/specification
REQUEST_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "JSON-RPC Request Schema",
    "description": "JSON-Schema that validates a JSON-RPC 2.0 request body (non-batch requests)",
    "type": "object",
    "required": ["jsonrpc", "method"],
    "properties": {
        "jsonrpc": {
            "const": "2.0"
        },
        "method": {
            "type": "string",
            "minLength": 1,
        },
        "id": {
            "type": ["integer", "string"]
        },
        "params": {
            "anyOf": [{"type": "object"}, {"type": "array"}]
        }
    }
}

# Reference: https://www.jsonrpc.org/specification#error_object
RPC_ERRORS = {
    # Invalid JSON was received. An error occurred on the server while parsing the JSON text.
    -32700: 'Parse error',
    # The JSON sent is not a valid Request object.
    -32600: 'Invalid Request',
    # The method does not exist / is not available.
    -32601: 'Method not found',
    # Invalid method parameter(s).
    -32602: 'Invalid params',
    # Internal JSON-RPC error.
    -32603: 'Internal error',
    # Reserved for implementation-defined server-errors.
    -32000: 'Server error',
}

log = logging.getLogger(__name__)


class JSONRPCService(object):
    """
    The JSONRPCService class is a JSON-RPC
    """

    def __init__(self):
        """
        Initialize a new JSONRPCService object.
        """
        # A mapping of method name to python function and json-schema
        self.method_data = {}

    def add(self, func: Callable, name: str = None, schema: Optional[dict] = None):
        """
        Adds a new method to the jsonrpc service. If name argument is not
        given, function's own name will be used.

        Example:
            service.add(myfunc, name='my_function', schema=param_schema)

        Args:
            func (function): required python function handler to call for this method
            name (str): optional name of the method (defaults to the function's name)
            schema (dict): optional JSON-Schema for parameter validation
        """
        fname = name if name else func.__name__
        if fname in self.method_data:
            raise exceptions.DuplicateMethodName(fname)
        self.method_data[fname] = {'method': func, 'schema': schema}

    def call(self, jsondata: str, metadata=None) -> str:
        """
        Calls jsonrpc service's method and returns its return value in a JSON
        string or None if there is none.

        Args:
           jsondata: JSON-RPC 2.0 request body (raw string)
           metadata: any additional object to pass along to the handler function as the second arg

        Returns:
            The JSON-RPC 2.0 response as a raw JSON string.
            Will not throw an exception.
        """
        try:
            request_data = json.loads(jsondata)
        except ValueError as err:
            resp = self._err_response(-32700, err_data={'details': str(err)}, always_respond=True)
            return json.dumps(resp)
        result = self.call_py(request_data, metadata)
        if result is not None:
            return json.dumps(result)

    def call_py(self, req_data, metadata=None) -> Optional[Union[dict, List[dict]]]:
        """
        Call a method in the service and return the RPC response. This behaves
        the same as call() except that the request and response are python
        objects instead of JSON strings.

        Args:
            req_data: JSON-RPC 2.0 request payload as a python object
            metadata: Any optional additional data to send to the handler function

        Returns:
            The JSON-RPC 2.0 response as a python object.
            Returns None if the request is a notification.
            Will not throw an exception.
        """
        if isinstance(req_data, list):
            if len(req_data) == 0:
                err_data = {'details': 'Batch request array is empty'}
                return self._err_response(-32600, err_data=err_data, always_respond=True)
            return self._call_batch(req_data, metadata)
        return self._call_single(req_data, metadata)

    def _call_single(self, req_data: dict, metadata) -> dict:
        """
        Make a single method call (used in call_py() and _call_batch())
        """
        try:
            jsonschema.validate(req_data, REQUEST_SCHEMA)
        except jsonschema.exceptions.ValidationError as err:
            log.exception(f'Invalid JSON-RPC request for {req_data}: {err}')
            return self._err_response(-32600, req_data,
                                      err_data={'details': err.message},
                                      always_respond=True)
        if req_data['method'] not in self.method_data:
            # Missing method
            meths = list(self.method_data.keys())
            err_data = {'available_methods': meths}
            return self._err_response(-32601, req_data, err_data=err_data)
        method = self.method_data[req_data['method']]['method']
        schema = self.method_data[req_data['method']]['schema']
        params = req_data.get('params')
        if schema is not None:
            try:
                jsonschema.validate(params, schema)
            except jsonschema.exceptions.ValidationError as err:
                # Invalid params error response
                err_data = {'details': err.message}
                return self._err_response(-32602, req_data, err_data)
        try:
            result = method(params, metadata)
        except Exception as err:
            # Exception was raised inside the method.
            log.exception(f"Method {req_data['method']} threw an exception: {err}")
            err_data = {'method': req_data['method']}
            if hasattr(err, 'message'):
                err_data['details'] = err.message
            code = -32000  # Server error
            if hasattr(err, 'jsonrpc_code'):
                code = err.jsonrpc_code
                if code > -32000 or code < -32099:
                    raise exceptions.InvalidServerErrorCode
            return self._err_response(code, req_data, err_data)
        _id = self._response_id(req_data)
        if type(_id) in (str, int):
            # Return the result in JSON-RPC 2.0 response format
            return {
                'id': _id,
                'jsonrpc': '2.0',
                'result': result,
            }
        else:
            # Notification request; no results
            return None

    def _call_batch(self, req_data: List[dict], metadata) -> Optional[List[dict]]:
        """
        Make many method calls (used in call_py())
        """
        results = []
        for req in req_data:
            resp = self._call_single(req, metadata)
            # According to the spec, notification requests do not go in the result array
            if resp is not None:
                results.append(resp)
        # Equivalent to something like `return results or None`, but let's be explicit:
        if len(results) == 0:
            # Every request was a notification
            return None
        else:
            return results

    def _err_response(self,
                      code: int,
                      req_data: Optional[dict] = None,
                      err_data: Optional[dict] = None,
                      always_respond: bool = False) -> dict:
        """
        Return a JSON-RPC 2.0 error response. The 'message' field is
        autopopulated from the code based on values from the spec.

        Args:
            code: JSON-RPC 2.0 error code
            req_data: Request data as a python object
            err_data: Optional 'data' field for the error response
            always_respond: Even if there was no ID in the request, send a response
        Returns:
            JSON-RPC 2.0 error response as a python dict
        """
        _id = self._response_id(req_data) if req_data else None
        if _id is None and not always_respond:
            # Do not return error responses for notifications
            return None
        resp = {
            'jsonrpc': '2.0',
            'id': _id,
            'error': {
                'code': code,
                'message': RPC_ERRORS[code],
            }
        }
        if err_data:
            resp['error']['data'] = err_data
        return resp

    def _response_id(self, req_data):
        """
        Get the ID for the response from the request
        Return None if ID is missing or invalid
        """
        _id = None
        if isinstance(req_data, dict):
            _id = req_data.get('id')
        if type(_id) in (str, int):
            return _id
        else:
            return None
