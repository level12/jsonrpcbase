"""
jsonrpcbase tests
"""
import pytest
import jsonrpcbase
import json
import jsonschema

s = jsonrpcbase.JSONRPCService(schema_path='test/test_schema.yaml', development=True)


def subtract(params, meta):
    return params[0] - params[1]


def kwargs_subtract(params, meta):
    return params['a'] - params['b']


def square(params, meta):
    return params[0] * params[0]


def hello(params, meta):
    return "Hello world!"


class Hello():
    def msg(self, params, meta):
        return "Hello world!"


def noop(params, meta):
    pass


def return_meta(params, meta):
    """Used to test metadata param"""
    return meta


def broken_func(params, meta):
    e = TypeError()
    e.message = 'whoops'
    raise e


s.add(subtract)
s.add(kwargs_subtract)
s.add(square)
s.add(hello)
s.add(Hello().msg, name='hello_inst')
s.add(noop)
s.add(broken_func)
s.add(return_meta)


def test_multiple_args():
    """
    Test valid jsonrpc multiple argument calls.
    """
    res_str = s.call('{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "1"}')
    result = json.loads(res_str)
    assert result['jsonrpc'] == "2.0"
    assert result['result'] == 19
    assert result['id'] == "1"


def test_kwargs():
    """
    Test valid jsonrpc keyword argument calls.
    """
    result = s.call_py({
        'jsonrpc': "2.0",
        'method': 'kwargs_subtract',
        'params': {'a': 42, 'b': 23},
        'id': "1"
    })
    assert result['jsonrpc'] == "2.0"
    assert result['result'] == 19
    assert result['id'] == "1"


def test_single_arg():
    """
    Test valid jsonrpc single argument calls.
    """
    result = s.call_py({
        "jsonrpc": "2.0",
        "method": "square",
        "params": [2],
        "id": "1"
    })
    assert result['jsonrpc'] == "2.0"
    assert result['result'] == 4
    assert result['id'] == "1"


def test_no_args():
    """
    Test valid jsonrpc no argument calls.
    """
    result = s.call_py({
        "jsonrpc": "2.0",
        "method": "hello",
        "id": "1"
    })
    assert result['jsonrpc'] == "2.0"
    assert result['result'] == "Hello world!"
    assert result['id'] == "1"


def test_metadata():
    """
    Test that metadata is passed to the function handler
    """
    req = '{"jsonrpc": "2.0", "method": "return_meta", "id": 0}'
    meta = {'x': 1}
    res = s.call(req, meta)
    result = json.loads(res)
    assert result['result'] == meta


def test_no_args_instance_method():
    """
    Test valid jsonrpc no argument calls on a class instance method.
    """
    result = s.call_py({
        "jsonrpc": "2.0",
        "method": "hello_inst",
        "id": "1"
    })
    assert result['jsonrpc'] == "2.0"
    assert result['result'] == "Hello world!"
    assert result['id'] == "1"


def test_empty_return():
    """
    Test valid jsonrpc empty return calls.
    """
    result = s.call_py({
        "jsonrpc": "2.0",
        "method": "noop",
        "params": [1, 2, 3, 4, 5],
        "id": 3
    })
    assert result['jsonrpc'] == "2.0"
    assert result['result'] is None
    assert result['id'] == 3


def test_notification():
    """
    Test valid notification jsonrpc calls.
    """
    result = s.call('{"jsonrpc": "2.0", "method": "noop", "params": [1,2,3,4,5]}')
    assert result is None


def test_parse_error():
    """
    Test parse error triggering invalid json messages.
    """
    # rpc call with invalid JSON
    req = """
    {
        "jsonrpc": "2.0",
        "method": "subtract",
        "params": "bar", "baz",
        "id": 0,
    }
    """
    res = s.call(req)
    result = json.loads(res)
    assert result['jsonrpc'] == "2.0"
    assert result['error']['code'] == -32700
    assert result['error']['data'] == {
        'details': "Expecting ':' delimiter: line 5 column 31 (char 93)"
    }
    assert result['id'] is None


def test_invalid_request_type():
    """
    Test error response for an invalid request type
    """
    res = s.call("null")
    result = json.loads(res)
    assert result['jsonrpc'] == "2.0"
    assert result['error']['code'] == -32600
    assert result['error']['message'] == 'Invalid Request'
    assert result['id'] is None


def test_invalid_method_type():
    """
    Test the error response for a request with an invalid method field type
    """
    req = """
    {
        "jsonrpc": "2.0",
        "method": 1,
        "params": {}
    }
    """
    res = s.call(req)
    result = json.loads(res)
    assert result['jsonrpc'] == "2.0"
    err = result['error']
    assert err['code'] == -32600
    assert err['message'] == 'Invalid Request'
    assert err['data']['details'] == "1 is not of type 'string'"
    assert result['id'] is None


def test_method_not_found_error():
    """
    Test method not found error triggering jsonrpc calls.
    """
    # rpc call of non-existent method
    result = s.call_py({
        "jsonrpc": "2.0",
        "method": "foofoo",
        "id": 1
    })
    meths = set(s.method_data.keys())
    assert result['jsonrpc'] == "2.0"
    assert result['error']['code'] == -32601
    assert result['error']['message'] == 'Method not found'
    assert set(result['error']['data']['available_methods']) == meths
    assert result['id'] == 1


def test_method_missing_error():
    """
    Test missing method error
    """
    result = s.call_py({"jsonrpc": "2.0", "id": 1})
    assert result['jsonrpc'] == "2.0"
    assert result['error']['code'] == -32600
    assert result['error']['message'] == 'Invalid Request'
    assert result['error']['data']['details'] == "'method' is a required property"


def test_server_error():
    """
    Test server error triggering jsonrpc calls.
    broken_func always raises
    """
    result = s.call_py({
        "jsonrpc": "2.0",
        "method": "broken_func",
        "params": [5],
        "id": "1"
    })
    assert result['jsonrpc'] == "2.0"
    assert result['id'] == "1"
    assert result['error']['code'] == -32000
    assert result['error']['message'] == 'Server error'
    errdat = result['error']['data']
    assert errdat['details'] == 'whoops'
    assert errdat['method'] == 'broken_func'


def test_invalid_id():
    """
    Test the error response for an invalid `id` field
    """
    res = s.call('{"jsonrpc": "2.0", "id": {}, "method": "noop", "params": {}}')
    result = json.loads(res)
    assert result['error']['message'] == 'Invalid Request'
    assert result['error']['code'] == -32600
    assert result['error']['data']['details'] == "{} is not of type 'integer', 'string'"
    assert 'result' not in result
    assert result['id'] is None


def test_invalid_params():
    """
    Test the error response for an invalid `params` field
    """
    res = s.call('{"jsonrpc": "2.0", "id": 0, "method": "noop", "params": "hi"}')
    result = json.loads(res)
    assert result['error']['message'] == 'Invalid Request'
    assert result['error']['data']['details'] == "'hi' is not of type 'object'"
    assert result['error']['code'] == -32600
    assert 'result' not in result
    assert result['id'] == 0


def test_invalid_version():
    """
    Test error response for invalid jsonrpc version
    """
    # Use default
    res = s.call('{"jsonrpc": "9999", "method": "noop", "params": {"kwarg": 5}}')
    result = json.loads(res)
    assert result['jsonrpc'] == "2.0"
    assert result['error']['code'] == -32600
    assert result['error']['message'] == 'Invalid Request'
    assert result['error']['data']['details'] == "'2.0' was expected"
    assert result['id'] is None


def test_version_response_parse_error():
    """
    Test the jsonrpc version in the response for a parse error
    """
    # Parse error
    # Assume "2.0" version because version could not be read
    res = s.call('{ "method": "echo", "params": "bar", "baz", "id": 1} ')
    result = json.loads(res)
    assert result['jsonrpc'] == "2.0"
    assert result['error']['code'] == -32700
    assert result['id'] is None


def test_version_response_no_version():
    """
    Test the jsonrpc version in the response when no version is supplied
    """
    # Use default
    res = s.call('{"method": "noop", "params": {"kwarg": 5}, "id": 6}')
    result = json.loads(res)
    assert result['id'] == 6
    assert result['jsonrpc'] == "2.0"
    assert result['error']['message'] == 'Invalid Request'
    assert result['error']['data'] == {'details': "'jsonrpc' is a required property"}


def test_batch():
    """
    Test valid jsonrpc batch calls, no notifications.
    """
    results = s.call_py([
        {"jsonrpc": "2.0", "method": "square", "params": [4], "id": "1"},
        {"jsonrpc": "2.0", "method": "subtract", "params": [12, 3], "id": "2"},
        {"jsonrpc": "2.0", "method": "noop", "id": "3"},
    ])
    assert len(results) == 3
    for result in results:
        assert result['jsonrpc'] == "2.0"
        if result['id'] == "1":
            assert result['result'] == 16
        if result['id'] == "2":
            assert result['result'] == 9
        if result['id'] == "3":
            assert result['result'] is None


def test_notification_batch():
    """
    Test valid jsonrpc notification only batch calls.
    """
    result = s.call_py([
        {"jsonrpc": "2.0", "method": "noop", "params": [1, 2, 4]},
        {"jsonrpc": "2.0", "method": "noop", "params": [7]},
    ])
    assert result is None


def test_batch_method_error_with_notification():
    result = s.call_py([
        {"jsonrpc": "2.0", "method": "broken_func"}
    ])
    assert result is None


def test_batch_method_missing_with_notification():
    """Unknown method in a batch call"""
    result = s.call_py([
        {"jsonrpc": "2.0", "method": "methodnotthere", "params": [7]},
    ])
    assert result is None


def test_empty_batch():
    """
    Test invalid empty jsonrpc batch call
    """
    result = s.call_py([])
    assert result['jsonrpc'] == "2.0"
    assert result['error']['code'] == -32600
    assert result['error']['message'] == 'Invalid Request'
    assert result['error']['data']['details'] == 'Batch request array is empty'
    assert result['id'] is None


def test_parse_error_batch():
    """
    Test parse error triggering invalid batch calls.
    """
    req = '[{"jsonrpc": "2.0", "method": xyz, "id": 0}]'
    res = s.call(req)
    result = json.loads(res)
    assert result['jsonrpc'] == "2.0"
    assert result['error']['code'] == -32700
    assert result['id'] is None


def test_invalid_batch():
    """
    Test invalid jsonrpc batch calls.
    Invalid request types.
    """
    results = s.call_py([1, 2, 3])
    assert len(results) == 3
    for result in results:
        assert result['jsonrpc'] == "2.0"
        assert result['error']['code'] == -32600
        assert result['id'] is None


def test_partially_valid_batch():
    """
    Test partially valid jsonrpc batch calls.
    """
    results = s.call_py([
        {"jsonrpc": "2.0", "method": "square", "params": [2], "id": 1},
        {"jsonrpc": "2.0", "method": "noop", "params": [7]},
        {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
        {"foo": "boo"},
        {"jsonrpc": "2.0", "method": "foo.get", "params": {"name": "myself"}, "id": "5"},
        {"jsonrpc": "2.0", "method": "broken_func", "params": [5], "id": "9"}
    ])
    assert len(results) == 5
    for result in results:
        assert result['jsonrpc'] == "2.0"
        if result['id'] == "1":
            assert result['result'] == 4
        elif result['id'] == "2":
            assert result['result'] == 19
        elif result['id'] == "5":
            assert result['error']['code'] == -32601
        elif result['id'] == "9":
            assert result['error']['code'] == -32000
        elif result['id'] is None:
            assert result['error']['code'] == -32600


def test_alternate_name():
    """
    Test method calling with alternate name.
    """
    def finnish_hello(params, meta):
        return "Hei maailma!"
    s.add(finnish_hello, name="fihello")
    result = s.call_py({"jsonrpc": "2.0", "method": "fihello", "id": "1"})
    assert result['jsonrpc'] == "2.0"
    assert result['result'] == "Hei maailma!"
    assert result['id'] == "1"


def test_positional_validation():
    """
    Test validation of positional arguments with valid jsonrpc calls.
    """
    s.add(noop, name='posv')
    result = s.call_py({
        "jsonrpc": "2.0",
        "method": "posv",
        "params": ["foo", 5, 6.0, True, False],
        "id": "1"
    })
    assert result['jsonrpc'] == "2.0"
    assert result['result'] is None
    assert result['id'] == "1"


def test_positional_validation_error():
    """
    Test error handling of validation of positional arguments with invalid jsonrpc calls.
    """
    result = s.call_py({
        "jsonrpc": "2.0",
        "method": "posv",
        "params": ["x", 1, 2.0, True, "x"],
        "id": "1",
    })
    assert result['jsonrpc'] == "2.0"
    assert result['error']['code'] == -32602
    assert result['error']['message'] == 'Invalid params'
    assert result['error']['data']['details'] == "'x' is not of type 'boolean'"
    assert result['id'] == "1"


def test_keyword_validation():
    """
    Test validation of keyword arguments with valid jsonrpc calls.
    """
    s.add(noop, name='keyv')
    result = s.call_py({
        "jsonrpc": "2.0",
        "method": "keyv",
        "params": {"a": 1, "b": False, "c": 6.0},
        "id": "1",
    })
    assert result['jsonrpc'] == "2.0"
    assert result['result'] is None
    assert result['id'] == "1"


def test_required_keyword_validation_error():
    """
    Test error handling of validation of required keyword arguments with invalid jsonrpc calls.
    """
    result = s.call_py({
        "jsonrpc": "2.0",
        "method": "keyv",
        # Missing required property "c"
        "params": {"a": 1, "b": 6.0},
        "id": "1"
    })
    assert result['jsonrpc'] == "2.0"
    assert result['error']['code'] == -32602
    assert result['error']['message'] == 'Invalid params'
    assert result['error']['data']['details'] == "'c' is a required property"
    assert result['id'] == "1"


def test_result_schema_validation():
    def echo(params, meta):
        return params['x']
    s.add(echo)
    with pytest.raises(jsonschema.exceptions.ValidationError):
        result = s.call_py({
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"x": "hi"}
        })
        assert result['error']['message'] == "'x' is not of type integer"


def test_duplicate_method_name_err():
    """
    Test the error raised when trying to add a pre-existing method name
    """
    with pytest.raises(jsonrpcbase.exceptions.DuplicateMethodName) as excinfo:
        s.add(noop)
    assert str(excinfo.value) == "Duplicate method name for JSON-RPC service: 'noop'"


def test_invalid_server_err_code():
    """Test the error when a user sets an invalid server error code"""
    class InvalidServerCode(Exception):
        jsonrpc_code = -100

    def invalid_server_code(params, meta):
        raise InvalidServerCode
    s.add(invalid_server_code)
    with pytest.raises(jsonrpcbase.exceptions.InvalidServerErrorCode):
        s.call_py({"method": "invalid_server_code", "jsonrpc": "2.0"})


def test_invalid_service_schema():
    with pytest.raises(jsonrpcbase.exceptions.InvalidSchemaError):
        jsonrpcbase.JSONRPCService(schema_path='test/invalid_schema.json')
    with pytest.raises(jsonrpcbase.exceptions.InvalidSchemaError):
        jsonrpcbase.JSONRPCService(schema_path='test/xyz.txt')
