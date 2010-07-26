"""
jsonrpcbase tests
"""

import jsonrpcbase
from nose.tools import *

test_service = jsonrpcbase.JSONRPCService()

@test_service()
def subtract(a, b):
    return a - b

@test_service()
def kwargs_subtract(**kwargs):
    return kwargs['a'] - kwargs['b']

@test_service()
def square(a):
    return a * a

@test_service()
def hello():
    return "Hello world!"

@test_service()
def noop(*args, **kwargs):
    pass

@test_service()
def broken_func(a):
    raise TypeError
    
def test_multiple_args():
    """
    Test valid jsonrpc multiple argument calls.
    """
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "subtract", "params": [42, 23], "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['result'], 19)
    assert_equal(result['id'], "1")

def test_kwargs():
    """
    Test valid jsonrpc keyword argument calls.
    """
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "kwargs_subtract", "params": {"a":42, "b":23}, "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['result'], 19)
    assert_equal(result['id'], "1")

def test_single_arg():
    """
    Test valid jsonrpc single argument calls.
    """
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "square", "params": [2], "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['result'], 4)
    assert_equal(result['id'], "1")
    
def test_no_args():
    """
    Test valid jsonrpc no argument calls.
    """
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "hello", "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['result'], "Hello world!")
    assert_equal(result['id'], "1")
    
def test_empty_return():
    """
    Test valid jsonrpc empty return calls.
    """
    result = test_service.call_py('{"jsonrpc": "2.0", "method": "noop", "params": [1,2,3,4,5], "id":3}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['result'], None)
    assert_equal(result['id'], 3)

def test_notification():
    """
    Test valid notification jsonrpc calls.
    """
    result = test_service.call_py('{"jsonrpc": "2.0", "method": "noop", "params": [1,2,3,4,5]}')
    assert_equal(result, None)
    
    result = test_service.call_py('{"jsonrpc": "2.0", "method": "hello"}')
    assert_equal(result, None)
    
def test_parse_error():
    """
    Test parse error triggering invalid json messages.
    """
    #rpc call with invalid JSON
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "subtract, "params": "bar", "baz]')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32700)
    assert_equal(result['id'], None)
    
def test_invalid_request_error():
    """
    Test invalid request error triggering invalid jsonrpc calls.
    """
    #rpc call with invalid Request object
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": 1, "params": "bar"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32600)
    assert_equal(result['id'], None)
    
def test_method_not_found_error():
    """
    Test method not found error triggering jsonrpc calls.
    """
    #rpc call of non-existent method
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "foofoo", "id": 1}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32601)
    assert_equal(result['id'], 1)
    
def test_pos_num_args_error():
    """
    Test error handling of positional arguments with jsonrpc calls having wrong amount of arguments.
    """
    # too few params
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "subtract", "params": [1], "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32602)
    assert_equal(result['id'], "1")
    
    # too many params
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "subtract", "params": [1, 2, 3], "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32602)
    assert_equal(result['id'], "1")
    
def test_server_error():
    """
    Test server error triggering jsonrpc calls.
    """
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "broken_func", "params": [5], "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32000)
    assert_equal(result['id'], "1")
    
def test_version_handling():
    """
    Test version handling with jsonrpc calls.
    """
    result = test_service.call_py('{"jsonrpc": "9999", "method": "noop", "params": {"kwarg": 5}}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32600)
    assert_equal(result['id'], None)
    
    result = test_service.call_py('{"jsonrpc": "2.0", "method": "noop", "params": {"kwarg": 5}}')
    
    assert_equal(result, None)
    
    result = test_service.call_py('{"version": "1.1", "method": "noop", "params": {"kwarg": 5}}')
    
    assert_equal(result, None)
    
    # trigger parse error
    result = test_service.call_py('{ "method": "echo", "params": "bar", "baz", "id": 1} ')
    
    # assume DEFAULT_JSONRPC version because version could not be read
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32700)
    assert_equal(result['id'], None)
    
    result = test_service.call_py('{"method": "foofoo", "params": [5], "id": 3}')
    
    assert_equal(result['id'], 3)
    assert_not_equal(result['error'], None)
    assert_equal(result['result'], None)
    
    #  there should be error response
    result = test_service.call_py('{"method": "noop", "params": {"kwarg": 5}, "id": 6}')
    
    assert_equal(result['id'], 6)
    assert_not_equal(result['error'], None)
    assert_equal(result['result'], None)
    
    # there should be no answer to a notification
    result = test_service.call_py('{"method": "noop", "params": {"kwarg": 5}}')
    
    assert_equal(result, None)
    
def test_batch():
    """
    Test valid jsonrpc batch calls, no notifications.
    """
    results = test_service.call_py('''
    [
        {"jsonrpc": "''' + jsonrpcbase.DEFAULT_JSONRPC + '''", "method": "square", "params": [4], "id": "1"},
        {"jsonrpc": "''' + jsonrpcbase.DEFAULT_JSONRPC + '''", "method": "subtract", "params": [12,3], "id": "2"},
        {"jsonrpc": "''' + jsonrpcbase.DEFAULT_JSONRPC + '''", "method": "noop", "id": "3"}
    ]
    ''')
    
    assert_equal(len(results), 3)
    
    for result in results:
        assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
        
        if result['id'] == "1":
            assert_equal(result['result'], 16)
        if result['id'] == "2":
            assert_equal(result['result'], 9)
    
def test_notification_batch():
    """
    Test valid jsonrpc notification only batch calls.
    """
    result = test_service.call_py('''
    [
        {"jsonrpc": "''' + jsonrpcbase.DEFAULT_JSONRPC + '''", "method": "noop", "params": [1,2,4]},
        {"jsonrpc": "''' + jsonrpcbase.DEFAULT_JSONRPC + '''", "method": "noop", "params": [7]}
    ]
    ''')
    
    assert_equal(result, None)
        
def test_empty_batch():
    """
    Test invalid empty jsonrpc calls.
    """
    #rpc call with an empty Array
    result = test_service.call_py('[]')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32600)
    assert_equal(result['id'], None)
    
def test_parse_error_batch():
    """
    Test parse error triggering invalid batch calls.
    """
    result = test_service.call_py('[ {"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                      '", "method": "sum", "params": [1,2,4], "id": "1"},{"jsonrpc": "2.0", "method" ]')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32700)
    assert_equal(result['id'], None)
    
def test_invalid_batch():
    """
    Test invalid jsonrpc batch calls.
    """
    results = test_service.call_py('[1,2,3]')
    
    assert_equal(len(results), 3)
    
    
    print results
    for result in results:
        assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
        assert_equal(result['error']['code'], -32600)
        assert_equal(result['id'], None)
        
def test_partially_valid_batch():
    """
    Test partially valid jsonrpc batch calls.
    """
    results = test_service.call_py('''
    [
        {"jsonrpc": "''' + jsonrpcbase.DEFAULT_JSONRPC + '''", "method": "square", "params": [2], "id": "1"},
        {"jsonrpc": "''' + jsonrpcbase.DEFAULT_JSONRPC + '''", "method": "noop", "params": [7]},
        {"jsonrpc": "''' + jsonrpcbase.DEFAULT_JSONRPC + '''", "method": "subtract", "params": [42,23], "id": "2"},
        {"foo": "boo"},
        {"jsonrpc": "''' + jsonrpcbase.DEFAULT_JSONRPC + '''", "method": "foo.get", "params": {"name": "myself"}, "id": "5"},
        {"jsonrpc": "''' + jsonrpcbase.DEFAULT_JSONRPC + '''", "method": "broken_func", "params": [5], "id": "9"} 
    ]
    ''')
    
    assert_equal(len(results), 5)
    
    for result in results:
        assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
        
        if result['id'] == "1":
            assert_equal(result['result'], 4)
        elif result['id'] == "2":
            assert_equal(result['result'], 19)
        elif result['id'] == "5":
            assert_equal(result['error']['code'], -32601)
        elif result['id'] == "9":
            assert_equal(result['error']['code'], -32000)
        elif result['id'] == None:
            assert_equal(result['error']['code'], -32600)
            
def test_alternate_name():
    """
    Test method calling with alternate name.
    """
    @test_service(name="fihello")
    def finnish_hello():
        return "Hei maailma!"
    
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "fihello", "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['result'], "Hei maailma!")
    assert_equal(result['id'], "1")
    
def test_method_adding():
    """
    Test method adding with the add() method instead of decorator.
    """
    def german_hello():
        return "Hallo Welt!"
    
    test_service.add(german_hello, "gerhello")
    
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "gerhello", "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['result'], "Hallo Welt!")
    assert_equal(result['id'], "1")
    
def test_positional_validation():
    """
    Test validation of positional arguments with valid jsonrpc calls.
    """
    @test_service(types=[basestring, int, float, bool, bool, int])
    def posv(a, b, c, d, e, f=6):
        return
    
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "posv", "params": ["foo", 5, 6.0, true, false], "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['result'], None)
    assert_equal(result['id'], "1")
    
def test_positional_validation_error():
    """
    Test error handling of validation of positional arguments with invalid jsonrpc calls.
    """
    @test_service(types=[int, bool, float])
    def pose(a, b, c):
        return
    
    # third argument is int, not float.
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "pose", "params": [1, false, 6], "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32602)
    assert_equal(result['id'], "1")
    
def test_keyword_validation():
    """
    Test validation of keyword arguments with valid jsonrpc calls.
    """
    @test_service(types={'a':int, 'b': bool, 'c': float})
    def keyv(**kwargs):
        return
    
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "keyv", "params": {"a": 1, "b": false, "c": 6.0}, "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['result'], None)
    assert_equal(result['id'], "1")
    
def test_keyword_validation_error():
    """
    Test error handling of validation of keyword arguments with invalid jsonrpc calls.
    """
    @test_service(types={'a':int, 'b': bool, 'c': float})
    def keye(**kwargs):
        return
    
    # kwarg 'c' is int, not float.
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "keye", "params": {"a": 1, "b": false, "c": 6}, "id": "1"}')
    print result
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32602)
    assert_equal(result['id'], "1")
    
def test_required_keyword_validation():
    """
    Test validation of required keyword arguments with valid jsonrpc calls.
    """
    @test_service(types={'a':int, 'b': bool, 'c': float}, required=['a','c'])
    def reqv(**kwargs):
        return
    
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "reqv", "params": {"a": 1, "c": 6.0}, "id": "1"}')
    
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['result'], None)
    assert_equal(result['id'], "1")
    
def test_required_keyword_validation_error():
    """
    Test error handling of validation of required keyword arguments with invalid jsonrpc calls.
    """
    @test_service(types={'a':int, 'b': bool, 'c': float}, required=['a', 'b', 'c'])
    def reqe(**kwargs):
        return
    
    result = test_service.call_py('{"jsonrpc": "' + jsonrpcbase.DEFAULT_JSONRPC + 
                                              '", "method": "reqe", "params": {"a": 1, "c": 6.0}, "id": "1"}')
    print result
    assert_equal(result['jsonrpc'], jsonrpcbase.DEFAULT_JSONRPC)
    assert_equal(result['error']['code'], -32602)
    assert_equal(result['id'], "1")

if __name__ == '__main__':
    import nose
    nose.main()
