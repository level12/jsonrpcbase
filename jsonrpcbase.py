# -*- coding: utf-8 -*-

# The MIT License
#
# Copyright (c) 2010 Juhani Åhman <juhani.ahman@cs.helsinki.fi>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
The jsonrpcbase implements a simple JSON-RPC service with the exception of a transport layer.

This library is intended as an auxiliary library for easy an implementation of JSON-RPC services with Unix/TCP socket 
like transport protocols that do not have complex special requirements. You need to utilize some suitable transport 
protocol with this library to actually provide a working JSON-RPC service.

Features:
- Supports JSON-RPC v2.0. Compatible with v1.x style calls with the exception of v1.0 class-hinting.
- Easy to use.
- Small size.
- Well tested.

Example:

    import jsonrpcbase
    
    chat_service = jsonrpcbase.JSONRPCService()
    
    @chat_service()
    def login(username, password):
        (...)
        return True
    
    # Adds the method receive_message to the service as a 'recv_msg'.
    @chat_service('recv_msg')
    def receive_message(**kwargs):
        (...)
        return chat_message
    
    def send_message(msg):
        (...)
        
    if __name__ == '__main__':
    
        # Alternate way of adding remote methods
        # Add the method send_message as a 'send_msg' to the service.
        chat_service.add(send_message, 'send_msg')
        
        (...)
        
        # Receive a JSON-RPC call.
        jsonrpc_call = my_socket.recv()
        
        # Process the JSON-RPC call.
        result = chat_service.call(jsonrpc_call)
        
        # Send back results.
        my_socket.send(result)
"""
import sys
from functools import wraps

# JSON library importing
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        raise ImportError('Your system has no json (included in Python v2.6 or later) or simplejson module available.')

DEFAULT_JSONRPC = '2.0'

class JSONRPCService(object):
    """
    The JSONRPCService class is a JSON-RPC
    """
    
    def __init__(self):
        self.methods = {}
    
    if sys.version_info >= (2, 4):
        def __call__(self, name=None):
            """
            Decorator function for adding remote methods.
            """
            def decorator(f):
                @wraps(f)
                def wrapper(*args, **kwargs):
                    return f(*args, **kwargs)
        
                self.add(f, name)
        
                return wrapper
            return decorator

    def add(self, f, name=None):
        """
        Adds a new method to the jsonrpc service.
        
        Arguments:
        f -- the remote function
        name -- name of the method in the jsonrpc service
        
        If name argument is not given, function's own name will be used.
        """
        if name is None:
            fname = f.__name__  # Register the function using its own name.
        else:
            fname = name

        self.methods[fname] = f
        
    def call(self, jsondata):
        """
        Calls jsonrpc service's method and returns its return value in a JSON string or None if there is none.
        
        Arguments:
        jsondata -- remote method call in jsonrpc format
        """
        return json.dumps(self.call_py(jsondata))

    def call_py(self, jsondata):
        """
        Calls jsonrpc service's method and returns its return value in python object format or None if there is none.
        
        This method is same as call() except the return value is a python object instead of JSON string. This method
        is mainly only useful for debugging purposes.
        """
        try:
            try:
                rdata = json.loads(jsondata)
            except ValueError:
                raise ParseError
        except ParseError, e:
            return self._get_err(e)

        # set some default values for error handling
        request = self._get_default_vals()

        try:
            if isinstance(rdata, dict) and rdata:
                # It's a single request.
                self._fill_request(request, rdata)
                respond = self._handle_request(request)

                # Don't respond to notifications
                if respond is None:
                    return None

                return respond
            elif isinstance(rdata, list) and rdata:
                # It's a batch.
                requests = []
                responds = []
                
                for rdata_ in rdata:
                    # set some default values for error handling
                    request_ = self._get_default_vals()
                    try:
                        self._fill_request(request_, rdata_)
                    except InvalidRequestError, e:
                        responds.append(self._get_err(e, request_['id']))
                        continue
                    except JSONRPCError, e:
                        responds.append(self._get_err(e,
                                                 request_['id'],
                                                 request_['jsonrpc']))
                        continue
                    
                    requests.append(request_)
                
                for request_ in requests:
                    try:
                        respond = self._handle_request(request_)
                    except JSONRPCError, e:
                        responds.append(self._get_err(e,
                                                 request_['id'],
                                                 request_['jsonrpc']))
                        continue
                    
                    # Don't respond to notifications
                    if respond is not None:
                        responds.append(respond)

                if responds:
                    return responds

                # Nothing to respond.
                return None
            else:
                # empty dict, list or wrong type
                raise InvalidRequestError
        
        except InvalidRequestError, e:
            return self._get_err(e, request['id'])
        except JSONRPCError, e:
            return self._get_err(e, request['id'], request['jsonrpc'])

    def _get_err(self, e, id=None, jsonrpc=DEFAULT_JSONRPC):
        """
        Returns jsonrpc error message.
        """
        # Do not respond to notifications when the request is valid.
        if not id and not isinstance(e, ParseError) and not isinstance(e, InvalidRequestError):
            return None
        
        respond = {'id': id}
        
        if isinstance(jsonrpc, int):
            # v1.0 requires result to exist always.
            # No error codes are defined in v1.0 so only use the message.
            if jsonrpc == 10:
                respond['result'] = None
                respond['error'] = e.dumps()['message']
            else:
                self._fill_ver(jsonrpc, respond)
                respond['error'] = e.dumps()
        else:
            respond['jsonrpc'] = jsonrpc
            respond['error'] = e.dumps()
        
        return respond

    def _fill_ver(self, iver, respond):
        """
        Fills version information to the respond from the internal integer version.
        """
        if iver == 20:
            respond['jsonrpc'] = '2.0'
        if iver == 11:
            respond['version'] = '1.1'

    def _man_args(self, f):
        """
        Returns number of mandatory arguments required by given function.
        """
        if f.func_defaults is None:
            return f.func_code.co_argcount

        return f.func_code.co_argcount - len(f.func_defaults)

    def _max_args(self, f):
        """
        Returns maximum number of arguments accepted by given function.
        """
        if f.func_defaults is None:
            return f.func_code.co_argcount

        return f.func_code.co_argcount + len(f.func_defaults)

    def _get_jsonrpc(self, rdata):
        """
        Returns jsonrpc request's jsonrpc value.

        InvalidRequestError will be raised if the jsonrpc value has invalid value.
        """
        try:
            if rdata['jsonrpc'] == '2.0':
                return 20
            else:
                # invalid version
                raise InvalidRequestError
        except (TypeError, KeyError):
            # It's probably a JSON-RPC v1.x style call.
            try:
                if rdata['version'] == '1.1':
                    return 11
            except (TypeError, KeyError):
                pass
        
        # Assume v1.0.
        return 10

    def _get_id(self, rdata):
        """
        Returns jsonrpc request's id value or None if there is none.

        InvalidRequestError will be raised if the id value has invalid type.
        """
        try:
            if isinstance(rdata['id'], basestring) or \
            isinstance(rdata['id'], int) or \
            isinstance(rdata['id'], long) or \
            isinstance(rdata['id'], float) or \
            rdata['id'] is None:
                return rdata['id']
            else:
                # invalid type
                raise InvalidRequestError
        except (TypeError, KeyError):
            # It's a notification.
            return None

    def _get_method(self, rdata):
        """
        Returns jsonrpc request's method value.

        InvalidRequestError will be raised if it's missing or is wrong type.
        MethodNotFoundError will be raised if a method with given method name does not exist.
        """
        try:
            if not isinstance(rdata['method'], basestring):
                raise InvalidRequestError
        except (TypeError, KeyError):
            raise InvalidRequestError

        if rdata['method'] not in self.methods.keys():
            raise MethodNotFoundError

        return self.methods[rdata['method']]

    def _get_params(self, rdata):
        """
        Returns a list of jsonrpc request's method parameters.
        """
        try:
            return rdata['params']
        except KeyError:
            return None

    def _fill_request(self, request, rdata):
        """Fills request with data from the jsonrpc call."""
        request['jsonrpc'] = self._get_jsonrpc(rdata)
        request['id'] = self._get_id(rdata)
        request['method'] = self._get_method(rdata)
        request['params'] = self._get_params(rdata)

    def _call_method(self, request):
        """Calls given method with given params and returns it value."""
        method = request['method']
        params = request['params']
        try:
            if isinstance(params, list):
                if self._man_args(method) > len(params) <= self._max_args(method):
                    raise InvalidParamsError

                return method(*params)
            elif isinstance(params, dict):
                if self._man_args(method) > len(params) <= self._max_args(method):
                    raise InvalidParamsError
                
                # Do not accept keyword arguments if the jsonrpc version is not >=1.1.
                if request['jsonrpc'] < 11:
                    raise KeywordError

                return method(**params)
            elif params is None:
                if self._man_args(method) > 0:
                    raise InvalidParamsError

                return method()
            else:
                raise InvalidParamsError
        except JSONRPCError:
            raise
        except Exception:
            # Exception was raised inside the method.
            raise ServerError

    def _handle_request(self, request):
        """Handles given request and returns its response."""
        result = self._call_method(request)

        # Do not respond to notifications.
        if not request['id']:
            return None

        respond = {}
        self._fill_ver(request['jsonrpc'], respond)
        respond['result'] = result
        respond['id'] = request['id']

        return respond

    def _get_default_vals(self):
        """Returns dictionary containing default jsonrpc request/responds values for error handling purposes."""
        return {"jsonrpc": DEFAULT_JSONRPC, "id": None}


class JSONRPCError(Exception):
    """
    JSONRPCError class based on the JSON-RPC 2.0 specs.

    code - number
    message - string
    data - object
    """
    code = 0
    message = None
    data = None

    def __init__(self, message=None):
        """Setup the Exception and overwrite the default message."""
        if message is not None:
            self.message = message

    def dumps(self):
        """Return the Exception data in a format for JSON-RPC."""

        error = {'code': self.code,
                'message': str(self.message)}

        if self.data != None:
            error['data'] = self.data

        return error


#===============================================================================
# Exceptions
#
# The error-codes -32768 .. -32000 (inclusive) are reserved for pre-defined
# errors.
#
# Any error-code within this range not defined explicitly below is reserved
# for future use
#===============================================================================

class ParseError(JSONRPCError):
    """Invalid JSON. An error occurred on the server while parsing the JSON text."""
    code = -32700
    message = 'Parse error'


class InvalidRequestError(JSONRPCError):
    """The received JSON is not a valid JSON-RPC Request."""
    code = -32600
    message = 'Invalid request'


class MethodNotFoundError(JSONRPCError):
    """The requested remote-procedure does not exist / is not available."""
    code = -32601
    message = 'Method not found'


class InvalidParamsError(JSONRPCError):
    """Invalid method parameters."""
    code = -32602
    message = 'Invalid params'


class InternalError(JSONRPCError):
    """Internal JSON-RPC error."""
    code = -32603
    message = 'Internal error'

# -32099..-32000 Server error. Reserved for implementation-defined server-errors.

class KeywordError(JSONRPCError):
    """The received JSON-RPC request is trying to use keyword arguments even tough its version is 1.0."""
    code = -32099
    message = 'Keyword argument error'
    
    
class ServerError(JSONRPCError):
    """Generic server error."""
    code = -32000
    message = 'Server error'
