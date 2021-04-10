import struct as struct #https://www.delftstack.com/howto/python/how-to-convert-bytes-to-integers/

class SessionVersion(object):

    def __init__(self, **kwargs): 
        self.__module = kwargs['module']
        self.__pc = kwargs['pc']
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
        self.__instr = None

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

    @property
    def instr(self):
        if self.__instr is None:
            m  = self.__module
            self.__instr = m.codes.addr(self.__pc)
        return self.__instr

    def clean_session(self, new_offset):
        aSerializer = self.device
        return aSerializer.clean_session(self.org_dump, self.org_vals, new_offset)

class DebugSession:

    def __init__(self):
        self.__sessions = []

    def get_current(self) -> SessionVersion:
        return self.__sessions[-1]

    def add(self, s: SessionVersion) -> None:
        self.__sessions.append(s)

    @property
    def device(self):
        return self.get_current().device

    @property
    def callstack(self):
        return self.get_current().callstack

    @property
    def stack_values(self):
        return self.get_current().stack_values

    @property
    def lin_mem(self):
        return self.get_current().lin_mem

    @property
    def table(self):
        return self.get_current().table

    @property
    def br_table(self):
        return self.get_current().br_table

    @property
    def opcode(self):
        return self.get_current().opcode


    @property
    def instr(self):
        return self.get_current().instr

    @property
    def globals(self):
        return self.get_current().globals

    @property
    def org_dump(self):
        return self.get_current().org_dump

    @property
    def org_vals(self):
        return self.get_current().org_vals

    def clean_session(self, new_offset):
        aSerializer = self.device
        return aSerializer.clean_session(self.org_dump, self.org_vals, new_offset)
