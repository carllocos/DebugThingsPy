from communication import protocol as ptc

def is_first_msg(msg):
    return isinstance(msg, ConfirmFirstMsg)

def is_run_msg(msg):
    return isinstance(msg, ConfirmRunMsg)

def is_halt_msg(msg):
    return isinstance(msg, ConfirmHaltMsg)

def is_add_bp_msg(msg):
    return isinstance(msg, ConfirmAddBP)

def is_rmv_bp_msg(msg):
    return isinstance(msg, ConfirmRemoveBP)

def is_at_bp_msg(msg):
    return isinstance(msg, AtBP)

def is_dump_msg(msg):
    return isinstance(msg, ConfirmDumpMsg)

def is_local_dump(msg):
    return isinstance(msg, ConfirmDumpLocals)

class FirstMsg(ptc.AMessageTemplate):
    NAME = 'dump'
    HEX = '10'

    def __init__(self):
        super().__init__(**{'name': FirstMsg.NAME, 'reply_template': ConfirmFirstMsg()})
        pl = FirstMsg.HEX + '\n'
        self.payload = pl.encode('ascii')


class ConfirmFirstMsg(ptc.AMessageTemplate):
    NAME = 'dump'
    HEX = '10'

    def __init__(self):
        super().__init__(**{'name': ConfirmFirstMsg.NAME})
        self.start =b'DUMP START\r\n'
        self.end=b'DUMP END\r\n'


class RunMsg(ptc.AMessageTemplate):
    NAME = 'run'
    HEX = '01'

    def __init__(self):
        super().__init__(**{'name': RunMsg.NAME, 'reply_template': ConfirmRunMsg()})
        pl = RunMsg.HEX + '\n'
        self.payload = pl.encode('ascii')


class ConfirmRunMsg(ptc.AMessageTemplate):
    NAME = 'run_confirm'

    def __init__(self):
        super().__init__(**{'name': RunMsg.NAME})
        self.start = b'GO!\r\n'


class HaltMsg(ptc.AMessageTemplate):
    NAME = 'halt'
    HEX = '02'

    def __init__(self):
        super().__init__(**{'name': HaltMsg.NAME, 'reply_template': ConfirmHaltMsg()})
        payload = HaltMsg.HEX + '\n'
        self.payload = payload.encode('ascii')


class ConfirmHaltMsg(ptc.AMessageTemplate):
    NAME = 'halt_confirm'

    def __init__(self):
        super().__init__(**{'name': RunMsg.NAME})
        self.start = b'STOP!\r\n'


class PauseMsg(ptc.AMessageTemplate):
    NAME = 'pause'
    HEX = '03'

    def __init__(self):
        super().__init__(**{'name': PauseMsg.NAME})
        payload = PauseMsg.HEX + '\n'
        self.payload = payload.encode('ascii')


class StepMsg(ptc.AMessageTemplate):
    NAME = 'step'
    HEX = '04'

    def __init__(self):
        super().__init__(**{'name': StepMsg.NAME})
        payload = StepMsg.HEX + '\n'
        self.payload = payload.encode('ascii')


class AddBreakPointMsg(ptc.AMessageTemplate):
    NAME = 'add_breakpoint'
    HEX = '06'

    def __init__(self, size_hex, addr_hex):
        super().__init__(**{'name': AddBreakPointMsg.NAME})
        _pl = AddBreakPointMsg.HEX + size_hex[2:] + addr_hex[2:] + '\n'
        self.payload = _pl.upper().encode('ascii')
        self.set_reply_template(ConfirmAddBP(addr_hex))


class ConfirmAddBP(ptc.AMessageTemplate):
    NAME = 'confirm_add_bp'

    def __init__(self, addr):
        super().__init__(**{'name': ConfirmAddBP.NAME, 'reply_template': AtBP(addr)})
        _start = f'ADD BP {addr}!\r\n'
        self.start = _start.encode('ascii')
        self.bp_addr = addr

class AtBP(ptc.AMessageTemplate):
    NAME = 'at_bp'
    def __init__(self, addr):
        super().__init__(**{'name': AtBP.NAME})
        _start = f'AT {addr}!\r\n'
        self.start = _start.encode('ascii')
        self.bp_addr = addr

class RemoveBreakPointMsg(ptc.AMessageTemplate):
    NAME = 'remove_breakpoint'
    HEX = '07'

    def __init__(self, size_hex, addr_hex):
        super().__init__(**{'name': RemoveBreakPointMsg.NAME})
        _pl = RemoveBreakPointMsg.HEX + size_hex[2:] + addr_hex[2:] + '\n'
        self.payload = _pl.upper().encode('ascii')
        self.set_reply_template(ConfirmRemoveBP(addr_hex))


class ConfirmRemoveBP(ptc.AMessageTemplate):
    NAME = 'confirm_remove_bp'

    def __init__(self, addr):
        super().__init__(**{'name': ConfirmRemoveBP.NAME})
        _start = f'RMV BP {addr}!\r\n'
        self.start = _start.encode('ascii')

class DumpMsg(ptc.AMessageTemplate):
    NAME = 'dump'
    HEX = '10'

    def __init__(self):
        super().__init__(**{'name': DumpMsg.NAME, 'reply_template': ConfirmDumpMsg()})
        self.payload = f'{DumpMsg.HEX}\n'.encode('ascii')

class ConfirmDumpMsg(ptc.AMessageTemplate):
    NAME = 'confirm_dump'

    def __init__(self):
        super().__init__(**{'name': ConfirmDumpMsg.NAME})
        _start = f'DUMP START\r\n'
        _end = f'DUMP END\r\n'
        self.start = _start.encode('ascii')
        self.end = _end.encode('ascii')

class DumpLocals(ptc.AMessageTemplate):
    NAME = 'dump_local'
    HEX = '11'

    def __init__(self, dump_msg = False):
        super().__init__(**{'name': DumpLocals.NAME, 'reply_template': ConfirmDumpLocals()})
        _pl = DumpLocals.HEX + '\n'
        self.payload = _pl.encode('ascii')
        self.dump_msg = dump_msg

class ConfirmDumpLocals(ptc.AMessageTemplate):
    NAME = 'confirm_dump_local'

    def __init__(self):
        super().__init__(**{'name': ConfirmDumpLocals.NAME})
        self.start = b'STACK START\r\n'
        self.end = b'STACK END\r\n'
