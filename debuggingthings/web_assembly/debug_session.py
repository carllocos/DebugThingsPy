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
        self.__original_dump = kwargs['org_dump']
        self.__original_vals = kwargs['org_vals']
        self.__device = kwargs['device']
        self.__serializer = kwargs['serializer']

    @property
    def serializer(self):
        return self.__serializer

    @property
    def device(self):
        return self.__device

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

    @property
    def org_dump(self):
        return self.__original_dump
    @property
    def org_vals(self):
        return self.__original_vals

    def clean_session(self, new_offset):
        aSerializer = self.serializer
        return aSerializer.clean_session(self.org_dump, self.org_vals, new_offset)
