from communication import protocol as ptc
from web_assembly import wa as WA
from web_assembly import WAModule, Expr
from boards import dummy
from things import ChangesHandler, DebugSession

class Debugger:
    def __init__(self, dev, wamodule = None):
        super().__init__()
        self.__device = dev
        self.__breakpoints = []
        self.__current_bp = False
        self.__advance_ctr = 0
        self.__received_session = False
        self.__changeshandler = ChangesHandler(wamodule)
        self.__wamodule = wamodule
        self.__debugsession = DebugSession()
        dev.debugger = self


    @property
    def changes_handler(self) -> ChangesHandler:
        return self.__changeshandler

    @property
    def device(self):
        return self.__device

    @property
    def module(self) -> WAModule:
        return self.__wamodule

    @property
    def current_bp(self):
        return self.__current_bp

    def give_offset(self):
        return self.device.vm.get_offset()

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

    def connect(self):
        c = self.device.connect()
        if not c:
            print(f"connection failed to {self.device.name}")
        else:
            print(f'connected to {self.device.name}') 

    def halt(self, code_info):
        print('received halt request')
        # state = State(self.__device, code_info)
        # _msgs = self.__serializer.halt(state)
        # print(f'received msgs {_msgs}')
        # self.__medium.send(_msgs, self.__device)

    def run(self):
        print('received run request')
        self.device.run()

    def pause(self, code_info):
        print("received paused request")
        # state = State(self.__device, code_info)
        # _msgs = self.__serializer.run(state)
        # self.__medium.send(_msgs, self.__device)

    def step(self, amount = 1):
        self.device.step(amount)
        _raw = self.device.step_state
        ds = WA.raw_to_stack(_raw, self.device, self.module)
        self.__debugsession.add(ds)
        if self.__changeshandler is not None:
            self.__changeshandler.change(ds) 
        return ds
        

    def ask_for_offset(self):
        self.device.ask_for_offset()

    def add_breakpoint(self, expr: Expr) -> None:
        self.device.add_breakpoint(expr.addr)

    def add_breakpoint_test(self, a:str, with_offset: bool = False) -> None:
        self.device.add_breakpoint_test(a, with_offset)
    # def add_breakpoint(self, addr, wait_for_at=True):
    #     code_info  = BreakPoint(addr)
    #     state = State(self.__device, code_info)
    #     _msgs = self.__serializer.add_breakpoint(state, wait_for_at)
    #     _reqs = self.__medium.send(_msgs, self.__device)
    #     self.__medium.wait_for_answers(_reqs)


    def remove_breakpoint(self, inst: Expr):
        self.device.remove_breakpoint(inst.addr)

    def update_fun(self, code_info):
        pass

    def commit(self):
        wasm = self.__changeshandler.commit()
        self.device.commit(wasm)
        
    def debug_session(self, code_info=False):
        if not self.__received_session and not self.__current_bp:
            print("no bp reached yet")
            return

        cbp = self.__current_bp
        if self.__received_session:
            cbp = self.device.specialbp()
            self.device.force_cbp(cbp)

        if not self.device.has_stack_for(cbp):
            self.device.debug_session()

        if self.__received_session:
            self.__received_session = False
            self.device.sync_with(cbp)

        _raw = self.device.get_callstack(self.__current_bp)
        ds = _raw and WA.raw_to_stack(_raw, self.device, self.module)
        self.__debugsession.add(ds)
        return self.__debugsession

    def receive_session(self, debugsess):
        self.__received_session = True
        cleaned = debugsess.clean_session(self.device.offset)
        # _session = self.device.serialize_session(cleaned)
        self.device.receive_session(cleaned)
        # _reqs = self.__medium.send(_msgs, self.__device)
        # self.__medium.wait_for_answers(_reqs)

    
    #FOR DEBUG
    # def get_med(self):
    #     return self.__medium
    # def get_encoder(self):
    #     return self.__serializer

    # def get_serial(self):
    #     return self.__medium.get_serial()

    # def to_bp(self, addr):
    #     self.remove_breakpoint(self.breakpoints()[0])
    #     self.add_breakpoint(addr, wait_for_at=False)
    #     self.__advance_ctr = self.__advance_ctr + 1
    #     self.run()

    #     #  print("Producing for At msg")
    #     #  print(self.get_serial().read_until(b'\n'))
    #     code_info  = BreakPoint(addr)
    #     state = State(self.__device, code_info)
    #     _msgs = self.__serializer.at_msg(state)
    #     _reqs = self.__medium.send(_msgs, self.__device)
    #     self.__medium.wait_for_answers(_reqs)

# class State:

#     def __init__(self, dev, code_info):
#         self.__dev = dev
#         self.__code_info = code_info

#     def device(self):
#         return self.__dev

#     def code_info(self):
#         return self.__code_info


# class BreakPoint:

#     def __init__(self, addr):
#         self.__addr = addr


    # def hex_addr(self):
    #     return self.__addr

# def intialize(self, code_info):
#     if not self.start_connection():
#         print('connection failed to start')
#         return

#     state = State(self.__device, code_info)
#     _msgs = self.__serializer.initialize_step(state)
#     _reqs = self.__medium.send(_msgs, self.__device)
#     self.__medium.wait_for_answers(_reqs)

# def start_connection(self):
#     return self.__medium.start_connection(self.__device)

    # def receive_session_test(self):
    #     self.__received_session = True
    #     dmp = dummy.dummy_dump['dump']
    #     vals = dummy.dummy_vals['local_dump']
    #     cleaned = self.__serializer.clean_session(dmp, vals, self.__serializer.get_offset())
    #     _msgs = self.__serializer.serialize_session(cleaned)
    #     _reqs = self.__medium.send(_msgs, self.__device)
    #     self.__medium.wait_for_answers(_reqs)