'''Asynchronous Redis Connection.

Requires pulsar_

.. _pulsar: http://packages.python.org/pulsar/
'''
from functools import partial

from pulsar import AsyncIOStream, Deferred

from .exceptions import ConnectionError
from . import connection



class AsyncRedisRequest(connection.RedisRequest, Deferred):
    
    def __init__(self, *args, **kwargs):
        Deferred.__init__(self)
        connection.RedisRequest.__init__(self, *args, **kwargs)
        
    def send(self, command):
        c = self.connection.connect()
        if c:
            return c.add_callback(lambda r : self._send(command,r), True)
        else:
            return self._send(command)
        
    def _send(self, command, conn_result = None):
        stream = self.connection.stream
        return stream.write(command,
                    lambda num_bytes : stream.read(self.parse))
                   
    def close(self):
        super(AsyncRedisRequest,self).close()
        self.callback(self.response)
    
    def add_errback(self, expected, error):
        return self.add_callback(partial(self.check_result,
                                         expected,error), True)
    
    def check_result(self, expected, error, result):
        if result != expected:
            raise error
        return result


class AsyncRedisConnection(connection.Connection):
    request_class = AsyncRedisRequest
    
    def _connect(self):
        self.stream = AsyncIOStream(self._sock)
        return self.stream.connect(self.address, self.on_connect)
        
    def on_connect(self, result = None):
        "Initialize the connection, authenticate and select a database"
        # if a password is specified, authenticate
        OK = b'OK'
        r = None
        if self.password:
            r = self.request('AUTH', self.password)\
                        .add_errback(OK,ConnectionError('Invalid Password'))

        # if a database is specified, switch to it
        if self.db:
            return r.add_callback(self.select) if r else self.select()
        else:
            return r
        
    def select(self, result = None):
        return self.request('SELECT', self.db)\
                .add_errback(OK, ConnectionError('Invalid Database'))
        