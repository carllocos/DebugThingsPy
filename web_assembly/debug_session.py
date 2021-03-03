import struct as struct #https://www.delftstack.com/howto/python/how-to-convert-bytes-to-integers/

class DebugSession(object):

    def __init__(self, **kwargs): 
        self.__cs = kwargs['callstack']
        self.__sv = kwargs['stack_values']
        self.__linmem = kwargs['lin_mem']
        self.__table = kwargs['table']
        self.__br_table = kwargs['br_table']
        self.__globals = kwargs['globals']
        self.__opcode = False  #kwargs['opcode']

    @property
    def callstack(self):
        return self.__cs

    @property
    def stack_values(self):
        return self.__sv

    @property
    def lin_mem(self):
        return self.__linmem

    @property
    def table(self):
        return self.__table

    @property
    def br_table(self):
        return self.__br_table

    @property
    def opcode(self):
        return self.__opcode

    @property
    def globals(self):
        return self.__globals
