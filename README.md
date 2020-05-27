# JSONRPCBase

> NOTE: This is a fork of [level12/jsonrpcbase](https://github.com/level12/jsonrpcbase/) with changes maintained by KBase

Simple JSON-RPC service without transport layer

This library is intended as an auxiliary library for easy an implementation of JSON-RPC services with Unix/TCP socket
like transport protocols that do not have complex special requirements. You need to utilize some suitable transport
protocol with this library to actually provide a working JSON-RPC service.

## Features

- Easy to use, small size, well tested.
- Supports JSON-RPC v2.0. Compatible with v1.x style calls with the exception of v1.0 class-hinting.
- Optional argument type validation that significantly eases development of jsonrpc method_data.

## Example

Example usage:

```py
import jsonrpcbase

chat_service = jsonrpcbase.JSONRPCService()

def login(username, password, timelimit=0):
    # (...)
    return True

def receive_message(**kwargs):
    # (...)
    return chat_message

def send_message(msg):
    # (...)
    pass

if __name__ == '__main__':

    # Adds the method login to the service as a 'login'.
    chat_service.add(login, types=[basestring, basestring, int])

    # Adds the method receive_message to the service as a 'recv_msg'.
    chat_service.add(receive_message, name='recv_msg', types={"msg": basestring, "id": int})

    # Adds the method send_message as a 'send_msg' to the service.
    chat_service.add(send_message, 'send_msg')

    # Receive a JSON-RPC call.
    jsonmsg = my_socket.recv()

    # Process the JSON-RPC call.
    result = chat_service.call(jsonmsg)

    # Send back results.
    my_socket.send(result)
```

## Development

Install [poetry](https://python-poetry.org/) and run `poetry install`.

Run tests with `make test`.

Deploy with `poetry build` and `poetry publish`.

## Credits

This project was originally developed by Juhani Åhman.
