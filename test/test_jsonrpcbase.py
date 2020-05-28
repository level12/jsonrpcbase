"""
jsonrpcbase tests
"""
import jsonrpcbase
import json

s = jsonrpcbase.JSONRPCService()
DEFAULT_JSONRPC = '2.0'


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


def broken_func(params, meta):
    raise TypeError


s.add(subtract)
s.add(kwargs_subtract)
s.add(square)
s.add(hello)
s.add(Hello().msg, name='hello_inst')
s.add(noop)
s.add(broken_func)


def test_multiple_args():
    """
    Test valid jsonrpc multiple argument calls.
    """
    res_str = s.call('{"jsonrpc": "'
                     + DEFAULT_JSONRPC
                     + '", "method": "subtract", "params": [42, 23], "id": "1"}')
    result = json.loads(res_str)
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['result'] == 19
    assert result['id'] == "1"


def test_kwargs():
    """
    Test valid jsonrpc keyword argument calls.
    """
    result = s.call_py('{"jsonrpc": "'
                       + DEFAULT_JSONRPC
                       + '", "method": "kwargs_subtract", "params": {"a":42, "b":23}, "id": "1"}')

    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['result'] == 19
    assert result['id'] == "1"


def test_single_arg():
    """
    Test valid jsonrpc single argument calls.
    """
    result = s.call_py('{"jsonrpc": "'
                       + DEFAULT_JSONRPC
                       + '", "method": "square", "params": [2], "id": "1"}')
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['result'] == 4
    assert result['id'] == "1"


def test_no_args():
    """
    Test valid jsonrpc no argument calls.
    """
    result = s.call_py('{"jsonrpc": "'
                       + DEFAULT_JSONRPC
                       + '", "method": "hello", "id": "1"}')

    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['result'] == "Hello world!"
    assert result['id'] == "1"


def test_no_args_instance_method():
    """
    Test valid jsonrpc no argument calls.
    """
    result = s.call_py('{"jsonrpc": "'
                       + DEFAULT_JSONRPC
                       + '", "method": "hello_inst", "id": "1"}')
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['result'] == "Hello world!"
    assert result['id'] == "1"


def test_empty_return():
    """
    Test valid jsonrpc empty return calls.
    """
    result = s.call_py('{"jsonrpc": "2.0", "method": "noop", "params": [1,2,3,4,5], "id":3}')
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['result'] is None
    assert result['id'] == 3


def test_notification():
    """
    Test valid notification jsonrpc calls.
    """
    result = s.call('{"jsonrpc": "2.0", "method": "noop", "params": [1,2,3,4,5]}')
    assert result is None
    result = s.call_py('{"jsonrpc": "2.0", "method": "hello"}')
    assert result is None


def test_parse_error():
    """
    Test parse error triggering invalid json messages.
    """
    # rpc call with invalid JSON
    result = s.call_py('{"jsonrpc": "' + DEFAULT_JSONRPC
                       + '", "method": "subtract, "params": "bar", "baz]')
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['error']['code'] == -32700
    assert result['id'] is None


def test_invalid_request_error():
    """
    Test invalid request error triggering invalid jsonrpc calls.
    """
    # rpc call with invalid Request object
    result = s.call_py('{"jsonrpc": "' + DEFAULT_JSONRPC
                       + '", "method": 1, "params": "bar"}')

    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['error']['code'] == -32600
    assert result['id'] is None


def test_method_not_found_error():
    """
    Test method not found error triggering jsonrpc calls.
    """
    # rpc call of non-existent method
    result = s.call_py('{"jsonrpc": "' + DEFAULT_JSONRPC
                       + '", "method": "foofoo", "id": 1}')

    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['error']['code'] == -32601
    assert result['id'] == 1


def test_server_error():
    """
    Test server error triggering jsonrpc calls.
    """
    result = s.call_py('{"jsonrpc": "' + DEFAULT_JSONRPC
                       + '", "method": "broken_func", "params": [5], "id": "1"}')

    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['error']['code'] == -32000
    assert result['id'] == "1"


def test_ver11_call():
    """
    Test a version 1.1 method call
    """
    result = s.call_py('{"version": "1.1", "id": 0, "method": "noop", "params": {}}')
    assert result['version'] == '1.1'
    assert result['result'] is None
    assert result['id'] == 0


def test_invalid_id():
    """
    Test the error response for an invalid `id` field
    """
    result = s.call_py('{"jsonrpc": "2.0", "id": {}, "method": "noop", "params": {}}')
    assert result['error'] == {'message': 'Invalid type for the `id` field', 'code': -32600}
    assert 'result' not in result
    assert result['id'] is None


def test_invalid_params():
    """
    Test the error response for an invalid `params` field
    """
    result = s.call_py('{"jsonrpc": "2.0", "id": 0, "method": "noop", "params": "hi"}')
    assert result['error'] == {'message': 'Invalid type for the `params` field', 'code': -32600}
    assert 'result' not in result
    assert result['id'] == 0


def test_version_handling():
    """
    Test version handling with jsonrpc calls.
    """
    # Use default
    result = s.call_py('{"jsonrpc": "9999", "method": "noop", "params": {"kwarg": 5}}')
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['error']['code'] == -32600
    assert result['id'] is None
    # Notification only
    result = s.call_py('{"jsonrpc": "2.0", "method": "noop", "params": {"kwarg": 5}}')
    assert result is None
    # Notification only
    result = s.call_py('{"version": "1.1", "method": "noop", "params": {"kwarg": 5}}')
    assert result is None
    # Parse error
    # Assume DEFAULT_JSONRPC version because version could not be read
    result = s.call_py('{ "method": "echo", "params": "bar", "baz", "id": 1} ')
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['error']['code'] == -32700
    assert result['id'] is None
    # Use default, unknown method
    result = s.call_py('{"method": "foofoo", "params": [5], "id": 3}')
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['id'] == 3
    assert result['error'] == {'code': -32601, 'message': 'Method not found'}
    assert 'result' not in result
    # Use default
    result = s.call_py('{"method": "noop", "params": {"kwarg": 5}, "id": 6}')
    assert result['id'] == 6
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert 'error' not in result
    assert result['result'] is None
    # there should be no answer to a notification
    result = s.call_py('{"method": "noop", "params": {"kwarg": 5}}')
    assert result is None


def test_batch():
    """
    Test valid jsonrpc batch calls, no notifications.
    """
    results = s.call_py(
        '''
    [
        {"jsonrpc": "''' + DEFAULT_JSONRPC
        + '''", "method": "square", "params": [4], "id": "1"},
        {"jsonrpc": "''' + DEFAULT_JSONRPC
        + '''", "method": "subtract", "params": [12,3], "id": "2"},
        {"jsonrpc": "''' + DEFAULT_JSONRPC + '''", "method": "noop", "id": "3"}
    ]
    ''')

    assert len(results) == 3

    for result in results:
        assert result['jsonrpc'] == DEFAULT_JSONRPC

        if result['id'] == "1":
            assert result['result'] == 16
        if result['id'] == "2":
            assert result['result'] == 9


def test_notification_batch():
    """
    Test valid jsonrpc notification only batch calls.
    """
    result = s.call_py(
        '''
    [
        {"jsonrpc": "''' + DEFAULT_JSONRPC
        + '''", "method": "noop", "params": [1,2,4]},
        {"jsonrpc": "''' + DEFAULT_JSONRPC + '''", "method": "noop", "params": [7]}
    ]
    ''')

    assert result is None


def test_batch_method_error_with_notification():
    result = s.call_py(
        '''
    [
        {"jsonrpc": "''' + DEFAULT_JSONRPC + '''", "method": "hello", "params": [7]}
    ]
    ''')
    assert result is None


def test_batch_method_missing_with_notification():
    result = s.call_py(
        '''
    [
        {"jsonrpc": "''' + DEFAULT_JSONRPC
        + '''", "method": "methodnotthere", "params": [7]}
    ]
    ''')
    assert result is None


def test_empty_batch():
    """
    Test invalid empty jsonrpc calls.
    """
    # rpc call with an empty Array
    result = s.call_py('[]')

    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['error']['code'] == -32600
    assert result['id'] is None


def test_parse_error_batch():
    """
    Test parse error triggering invalid batch calls.
    """
    result = s.call_py('[ {"jsonrpc": "' + DEFAULT_JSONRPC
                       + '", "method": "sum", "params": [1,2,4], "id": "1"}'
                       ',{"jsonrpc": "2.0", "method" ]')

    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['error']['code'] == -32700
    assert result['id'] is None


def test_invalid_batch():
    """
    Test invalid jsonrpc batch calls.
    """
    results = s.call_py('[1,2,3]')

    assert len(results) == 3

    for result in results:
        assert result['jsonrpc'] == DEFAULT_JSONRPC
        assert result['error']['code'] == -32600
        assert result['id'] is None


def test_partially_valid_batch():
    """
    Test partially valid jsonrpc batch calls.
    """
    results = s.call_py(
        '''
    [
        {"jsonrpc": "''' + DEFAULT_JSONRPC
        + '''", "method": "square", "params": [2], "id": "1"},
        {"jsonrpc": "''' + DEFAULT_JSONRPC + '''", "method": "noop", "params": [7]},
        {"jsonrpc": "''' + DEFAULT_JSONRPC
        + '''", "method": "subtract", "params": [42,23], "id": "2"},
        {"foo": "boo"},
        {"jsonrpc": "''' + DEFAULT_JSONRPC
        + '''", "method": "foo.get", "params": {"name": "myself"}, "id": "5"},
        {"jsonrpc": "''' + DEFAULT_JSONRPC
        + '''", "method": "broken_func", "params": [5], "id": "9"}
    ]
    ''')

    assert len(results) == 5

    for result in results:
        assert result['jsonrpc'] == DEFAULT_JSONRPC

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
    result = s.call_py('{"jsonrpc": "' + DEFAULT_JSONRPC
                       + '", "method": "fihello", "id": "1"}')
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['result'] == "Hei maailma!"
    assert result['id'] == "1"


def test_positional_validation():
    """
    Test validation of positional arguments with valid jsonrpc calls.
    """

    def posv(params, meta):
        return
    schema = {
        'type': 'array',
        'items': [
            {'type': 'string'},
            {'type': 'integer'},
            {'type': 'number'},
            {'type': 'boolean'},
            {'type': 'boolean'},
        ]
    }
    s.add(posv, schema=schema)
    result = s.call_py('{"jsonrpc": "' + DEFAULT_JSONRPC
                       + '", "method": "posv", "params": ["foo", 5, 6.0, true, false], "id": "1"}')
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['result'] is None
    assert result['id'] == "1"


def test_positional_validation_error():
    """
    Test error handling of validation of positional arguments with invalid jsonrpc calls.
    """

    def pose(params, meta):
        return
    schema = {
        'type': 'array',
        'items': [
            {'type': 'integer'},
            {'type': 'boolean'},
            {'type': 'number'},
        ]
    }
    s.add(pose, schema=schema)
    # third argument is str, not float.
    result = s.call_py('{"jsonrpc": "' + DEFAULT_JSONRPC
                       + '", "method": "pose", "params": [1, false, "x"], "id": "1"}')
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['error']['code'] == -32602
    assert result['id'] == "1"


def test_keyword_validation():
    """
    Test validation of keyword arguments with valid jsonrpc calls.
    """
    pass

    def keyv(params, meta):
        return
    schema = {
        'type': 'object',
        'properties': {
            'a': {'type': 'integer'},
            'b': {'type': 'boolean'},
            'c': {'type': 'number'},
        }
    }
    s.add(keyv, schema=schema)
    result = s.call_py('{"jsonrpc": "' + DEFAULT_JSONRPC + '", "method": "keyv", "params": {"a": 1, "b": false, "c": 6.0}, "id": "1"}')  # noqa
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['result'] is None
    assert result['id'] == "1"


def test_required_keyword_validation():
    """
    Test validation of required keyword arguments with valid jsonrpc calls.
    """

    def reqv(params, meta):
        return
    schema = {
        'type': 'object',
        'required': ['a', 'c'],
        'properties': {
            'a': {'type': 'integer'},
            'b': {'type': 'boolean'},
            'c': {'type': 'number'},
        }
    }
    s.add(reqv, schema=schema)
    result = s.call_py('{"jsonrpc": "' + DEFAULT_JSONRPC
                       + '", "method": "reqv", "params": {"a": 1, "c": 6.0}, "id": "1"}')

    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['result'] is None
    assert result['id'] == "1"


def test_required_keyword_validation_error():
    """
    Test error handling of validation of required keyword arguments with invalid jsonrpc calls.
    """
    pass

    def reqe(params, meta):
        return
    schema = {
        'type': 'object',
        'required': ['a', 'b', 'c'],
        'properties': {
            'a': {'type': 'integer'},
            'b': {'type': 'boolean'},
            'c': {'type': 'number'},
        }
    }
    s.add(reqe, schema=schema)
    result = s.call_py('{"jsonrpc": "' + DEFAULT_JSONRPC
                       + '", "method": "reqe", "params": {"a": 1, "c": 6.0}, "id": "1"}')
    assert result['jsonrpc'] == DEFAULT_JSONRPC
    assert result['error']['code'] == -32602
    assert result['id'] == "1"


if __name__ == '__main__':
    import nose
    nose.main()
