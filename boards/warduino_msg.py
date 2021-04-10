# from communication import protocol as ptc
# DUMP_START = b'DUMP START\r\n'
# DUMP_END = b'DUMP END\r\n'

# STACK_START = b'STACK START\r\n'
# STACK_END = b'STACK END\r\n'

# DUMP_BYTES  = b'BYTES\r\n'
# DUMP_BYTES_END  = b'BYTES END\r\n'

# def is_first_msg(msg):
#     return isinstance(msg, ConfirmFirstMsg)

# def is_table_bytes(msg):
#     return isinstance(msg, TableBytes)

# def is_rest_dump(msg):
#     return isinstance(msg, RestDump)

# def is_linmem(msg):
#     return isinstance(msg, LinMemBytes)

# def is_second_rest_dump(msg):
#     return isinstance(msg, SecondRestDump)

# def is_brtable_bytes(msg):
#     return isinstance(msg, BRTableBytes)

# def is_end_dump(msg):
#     return isinstance(msg, EndOfDump)

# def is_run_msg(msg):
#     return isinstance(msg, ConfirmRunMsg)

# def is_halt_msg(msg):
#     return isinstance(msg, ConfirmHaltMsg)

# def is_add_bp_msg(msg):
#     return isinstance(msg, ConfirmAddBP)

# def is_rmv_bp_msg(msg):
#     return isinstance(msg, ConfirmRemoveBP)

# def is_at_bp_msg(msg):
#     return isinstance(msg, AtBP)

# def is_dump_msg(msg):
#     return isinstance(msg, ConfirmDumpMsg)

# #  def is_some_hex(msg):
# #      return isinstance(msg, SomeHexElements)

# #  def is_some_end_dump(msg):
# #      return isinstance(msg, SomeEndOfDump)

# def is_local_dump(msg):
#     return isinstance(msg, ConfirmDumpLocals)

# def is_opcode(msg):
#     return isinstance(msg, Opcode)


# class FirstMsg(ptc.AMessageTemplate):
#     NAME = 'dump'
#     HEX = '10'

#     def __init__(self):
#         super().__init__(**{'name': FirstMsg.NAME, 'reply_template': ConfirmFirstMsg()})
#         pl = FirstMsg.HEX + '\n'
#         self.payload = pl.encode('ascii')

# class ConfirmFirstMsg(ptc.AMessageTemplate):
#     NAME = 'dump'
#     HEX = '10'

#     def __init__(self):
#         super().__init__(**{'name': ConfirmFirstMsg.NAME, 'reply_template': TableBytes()})
#         self.start =DUMP_START
#         self.end=DUMP_BYTES

# class TableBytes(ptc.AMessageTemplate):
#     NAME= 'TableBytes'

#     def __init__(self):
#         super().__init__(**{'name':TableBytes.NAME, 'reply_template': RestDump()})
#         self.end = DUMP_BYTES_END

# class RestDump(ptc.AMessageTemplate):
#     NAME='RestDump'

#     def __init__(self):
#         super().__init__(**{'name':RestDump.NAME, 'reply_template': LinMemBytes()})
#         self.end = DUMP_BYTES

# class LinMemBytes(ptc.AMessageTemplate):
#     NAME= 'LinMemBytes'

#     def __init__(self):
#         super().__init__(**{'name':LinMemBytes.NAME, 'reply_template': SecondRestDump()})
#         self.end = DUMP_BYTES_END

# class SecondRestDump(ptc.AMessageTemplate):
#     NAME='SecondRestDump'

#     def __init__(self):
#         super().__init__(**{'name':SecondRestDump.NAME, 'reply_template': BRTableBytes()})
#         self.end = DUMP_BYTES

# class BRTableBytes(ptc.AMessageTemplate):
#     NAME='BRTableBytes'

#     def __init__(self):
#         super().__init__(**{'name':BRTableBytes.NAME, 'reply_template': EndOfDump()})
#         self.end = DUMP_BYTES_END

# class EndOfDump(ptc.AMessageTemplate):
#     NAME='EndOfDump'

#     def __init__(self):
#         super().__init__(**{'name':EndOfDump.NAME})
#         self.end=DUMP_END

# class RunMsg(ptc.AMessageTemplate):
#     NAME = 'run'
#     HEX = '01'

#     def __init__(self):
#         super().__init__(**{'name': RunMsg.NAME, 'reply_template': ConfirmRunMsg()})
#         pl = RunMsg.HEX + '\n'
#         self.payload = pl.encode('ascii')


# class ConfirmRunMsg(ptc.AMessageTemplate):
#     NAME = 'run_confirm'

#     def __init__(self):
#         super().__init__(**{'name': RunMsg.NAME})
#         self.start = b'GO!\r\n'


# class HaltMsg(ptc.AMessageTemplate):
#     NAME = 'halt'
#     HEX = '02'

#     def __init__(self):
#         super().__init__(**{'name': HaltMsg.NAME, 'reply_template': ConfirmHaltMsg()})
#         payload = HaltMsg.HEX + '\n'
#         self.payload = payload.encode('ascii')


# class ConfirmHaltMsg(ptc.AMessageTemplate):
#     NAME = 'halt_confirm'

#     def __init__(self):
#         super().__init__(**{'name': RunMsg.NAME})
#         self.start = b'STOP!\r\n'


# class PauseMsg(ptc.AMessageTemplate):
#     NAME = 'pause'
#     HEX = '03'

#     def __init__(self):
#         super().__init__(**{'name': PauseMsg.NAME})
#         payload = PauseMsg.HEX + '\n'
#         self.payload = payload.encode('ascii')


# class StepMsg(ptc.AMessageTemplate):
#     NAME = 'step'
#     HEX = '04'

#     def __init__(self):
#         super().__init__(**{'name': StepMsg.NAME})
#         payload = StepMsg.HEX + '\n'
#         self.payload = payload.encode('ascii')


# class AddBreakPointMsg(ptc.AMessageTemplate):
#     NAME = 'add_breakpoint'
#     HEX = '06'

#     def __init__(self, size_hex, addr_hex, wait_for_at):
#         super().__init__(**{'name': AddBreakPointMsg.NAME})
#         _pl = AddBreakPointMsg.HEX + size_hex[2:] + addr_hex[2:] + '\n'
#         self.payload = _pl.upper().encode('ascii')
#         self.set_reply_template(ConfirmAddBP(addr_hex, wait_for_at))

#     @staticmethod
#     def print_str(size_hex, addr_hex):
#         print(f"got size_hex {size_hex} and addr {addr_hex}")
#         _pl = AddBreakPointMsg.HEX + size_hex[2:] + addr_hex[2:] + '\n'
#         return _pl.upper()

# class ConfirmAddBP(ptc.AMessageTemplate):
#     NAME = 'confirm_add_bp'

#     def __init__(self, addr, wait_for_at):
#         super().__init__(**{'name': ConfirmAddBP.NAME})
#         if wait_for_at:
#             self.set_reply_template(AtBP(addr))
#         _start = f'ADD BP {addr}!\r\n'
#         self.start = _start.encode('ascii')
#         self.bp_addr = addr

# class ForReceive(ptc.AMessageTemplate):
#     NAME = 'ForReceive'
#     def __init__(self, recv_msg):
#         super().__init__(**{'name': ForReceive.NAME, 'reply_template':recv_msg, 'to_send': False})

# class AtBP(ptc.AMessageTemplate):
#     NAME = 'at_bp'
#     def __init__(self, addr):
#         super().__init__(**{'name': AtBP.NAME})#, 'reply_template': Opcode()})
#         _start = f'AT {addr}!\r\n'
#         self.start = _start.encode('ascii')
#         self.bp_addr = addr

# #  class Opcode(ptc.AMessageTemplate):
# #      NAME = 'opcode'
# #      def __init__(self):
# #          super().__init__(**{'name': Opcode.NAME})
# #          _start = f'OPCODE!\r\n'
# #          self.start = _start.encode('ascii')
# #          self.end = 'END OPCODE\r\n'.encode('ascii')

# class RemoveBreakPointMsg(ptc.AMessageTemplate):
#     NAME = 'remove_breakpoint'
#     HEX = '07'

#     def __init__(self, size_hex, addr_hex):
#         super().__init__(**{'name': RemoveBreakPointMsg.NAME})
#         _pl = RemoveBreakPointMsg.HEX + size_hex[2:] + addr_hex[2:] + '\n'
#         self.payload = _pl.upper().encode('ascii')
#         self.set_reply_template(ConfirmRemoveBP(addr_hex))


# class ConfirmRemoveBP(ptc.AMessageTemplate):
#     NAME = 'confirm_remove_bp'

#     def __init__(self, addr_hex):
#         super().__init__(**{'name': ConfirmRemoveBP.NAME})
#         _start = f'RMV BP {addr_hex}!\r\n'
#         self.start = _start.encode('ascii')
#         self.bp_addr = addr_hex

# class DumpMsg(ptc.AMessageTemplate):
#     NAME = 'dump'
#     HEX = '10'

#     def __init__(self):
#         super().__init__(**{'name': DumpMsg.NAME, 'reply_template': ConfirmDumpMsg()})
#         self.payload = f'{DumpMsg.HEX}\n'.encode('ascii')

# class ConfirmDumpMsg(ptc.AMessageTemplate):
#     NAME = 'confirm_dump'

#     def __init__(self):
#         super().__init__(**{'name': ConfirmDumpMsg.NAME, 'reply_template': TableBytes()})
#         self.start =DUMP_START
#         self.end=DUMP_BYTES

# class SomeHexElements(ptc.AMessageTemplate):
#     NAME= 'SomeHexElements'

#     def __init__(self):
#         super().__init__(**{'name':SomeHexElements.NAME, 'reply_template': SomeEndOfDump()})
#         self.end = DUMP_BYTES_END

# class SomeEndOfDump(ptc.AMessageTemplate):
#     NAME='SomeEndOfDump'

#     def __init__(self):
#         super().__init__(**{'name':SomeEndOfDump.NAME})
#         self.end=DUMP_END

# class DumpLocals(ptc.AMessageTemplate):
#     NAME = 'dump_local'
#     HEX = '11'

#     def __init__(self, dump_msg = False):
#         super().__init__(**{'name': DumpLocals.NAME, 'reply_template': ConfirmDumpLocals()})
#         _pl = DumpLocals.HEX + '\n'
#         self.payload = _pl.encode('ascii')
#         self.dump_msg = dump_msg

# class ConfirmDumpLocals(ptc.AMessageTemplate):
#     NAME = 'confirm_dump_local'

#     def __init__(self):
#         super().__init__(**{'name': ConfirmDumpLocals.NAME})
#         self.start = STACK_START
#         self.end = STACK_END
