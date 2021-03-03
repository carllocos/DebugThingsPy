from communication import protocol as ptc
from web_assembly import wa as WA

class Debugger:
    def __init__(self, dev, serializer, medium):
        super().__init__()
        self.__device = dev
        self.__serializer = serializer
        serializer.set_debugger(self)
        self.__medium = medium
        self.__breakpoints = []
        self.__current_bp = False
        self.__advance_ctr = 0

    def current_bp(self):
        return self.__current_bp

    def give_offset(self):
        return self.__serializer.get_offset()

    def reset(self):
        self.remove_breakpoint(self.breakpoints()[0])
        self.run()

    def ack_add_bp(self, bp):
        print(f'Debugger: ack add bp: {bp}')
        self.__breakpoints.append(bp)

    def ack_rmv_bp(self, bp):
        print(f'Debugger: ack rmv bp: {bp}')
        self.__breakpoints = [p for p in self.__breakpoints if p != bp]

    def breakpoints(self):
        return self.__breakpoints

    def ack_current_bp(self, bp):
        print(f'Debugger: ack current bp: {bp}')
        self.__current_bp = bp

    def intialize(self, code_info):
        if not self.start_connection():
            print('connection failed to start')
            return

        state = State(self.__device, code_info)
        _msgs = self.__serializer.initialize_step(state)
        _reqs = self.__medium.send(_msgs, self.__device)
        self.__medium.wait_for_answers(_reqs)

    def start_connection(self):
        return self.__medium.start_connection(self.__device)

    def halt(self, code_info):
        print('received halt request')
        state = State(self.__device, code_info)
        _msgs = self.__serializer.halt(state)
        print(f'received msgs {_msgs}')
        self.__medium.send(_msgs, self.__device)

    def run(self, code_info=False):
        print('received run request')
        state = State(self.__device, code_info)
        _msgs = self.__serializer.run(state)
        _reqs = self.__medium.send(_msgs, self.__device)
        self.__medium.wait_for_answers(_reqs)

    def pause(self, code_info):
        state = State(self.__device, code_info)
        _msgs = self.__serializer.run(state)
        self.__medium.send(_msgs, self.__device)

    def step(self, code_info):
        state = State(self.__device, code_info)
        _msgs = self.__serializer.run(state)
        self.__medium.send(_msgs, self.__device)

    def add_breakpoint(self, addr, wait_for_at=True):
        code_info  = BreakPoint(addr)
        state = State(self.__device, code_info)
        _msgs = self.__serializer.add_breakpoint(state, wait_for_at)
        _reqs = self.__medium.send(_msgs, self.__device)
        self.__medium.wait_for_answers(_reqs)


    def remove_breakpoint(self, addr):
        code_info  = BreakPoint(addr)
        state = State(self.__device, code_info)
        _msgs = self.__serializer.remove_breakpoint(state)
        _reqs = self.__medium.send(_msgs, self.__device)
        self.__medium.wait_for_answers(_reqs)

    def update_fun(self, code_info):
        pass

    def debug_session(self, code_info=False):
        if not self.__current_bp:
            print("no bp reached yet")
            return

        #  print('current BP')
        #  print(self.__current_bp)
        if not self.__serializer.has_stack_for(self.__current_bp):
            state = State(self.__device, code_info)
            _msgs = self.__serializer.callstack_msgs(state)
            _reqs = self.__medium.send(_msgs, self.__device)
            self.__medium.wait_for_answers(_reqs)
        _raw = self.__serializer.get_callstack(self.__current_bp)
        #  print("RAW")
        #  print(_raw)
        return _raw and  WA.raw_to_stack(_raw)

    #FOR DEBUG
    def get_med(self):
        return self.__medium
    def get_encoder(self):
        return self.__serializer

    def get_serial(self):
        return self.__medium.get_serial()

    def to_bp(self, addr):
        self.remove_breakpoint(self.breakpoints()[0])
        self.add_breakpoint(addr, wait_for_at=False)
        self.__advance_ctr = self.__advance_ctr + 1
        self.run()

        #  print("Producing for At msg")
        #  print(self.get_serial().read_until(b'\n'))
        code_info  = BreakPoint(addr)
        state = State(self.__device, code_info)
        _msgs = self.__serializer.at_msg(state)
        _reqs = self.__medium.send(_msgs, self.__device)
        self.__medium.wait_for_answers(_reqs)

class State:

    def __init__(self, dev, code_info):
        self.__dev = dev
        self.__code_info = code_info

    def device(self):
        return self.__dev

    def code_info(self):
        return self.__code_info


class BreakPoint:

    def __init__(self, addr):
        self.__addr = addr


    def hex_addr(self):
        return self.__addr
