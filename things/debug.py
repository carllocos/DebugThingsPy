from __future__ import annotations
from typing import Union

from utils import valid_addr
from web_assembly import wa as WA
from web_assembly import WAModule, Expr
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
        self.__proxy_config = None
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
        pc = self.__proxy_config

        if pc is not None and len(pc.get('proxy', [])) > 0:
            self.device.send_proxies(pc)


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

    def commit(self, mod: Union[WAModule, None] = None):
        wasm = None
        if mod is not None:
            wasm = mod.compile()
        else:
            wasm = self.__changeshandler.commit()
        self.device.commit(wasm)


    def validate_proxyconfig(self, mod: WAModule, config: dict) -> dict:
        cleaned_config = {'proxy': [], 'host':None, 'port': None}
        if config.get('proxy', False):
            for n in config['proxy']:
                name = n
                #FIXME temporary cleanedup
                if isinstance(n, str) and n[0] == '$':
                    name = n[1:]
                f = mod.functions[name]
                if f is None:
                    raise ValueError(f'configuration error: proxy function `{name} is not declared in module')
                cleaned_config['proxy'].append(f.idx) 

        if config.get('host', False):
            if not valid_addr(config['host']):
                raise ValueError(f"configuration error: invalid host address `{config['addr']}")
            cleaned_config['host'] = config['host']
        if config.get('port', False):
            port = config['port']
            if not isinstance(port, int) or port <= 0:
                raise ValueError(f'configuration error: configured an incorrect port number for proxy requests')
            cleaned_config['port'] = port

        return cleaned_config

    def upload_proxies(self, proxy_config: Union[None, dict] = None) -> None:
        if proxy_config is None:
            proxy_config = self.__proxy_config
        if proxy_config is not None:
            self.device.send_proxies(proxy_config)
        
    def upload(self, mod: WAModule, config: dict) -> None:
        cleaned_config = self.validate_proxyconfig(mod, config)
        wasm = mod.compile()
        self.device.upload(wasm, cleaned_config)

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
        self.device.receive_session(cleaned)

    def add_proxyconfig(self, proxy_config: dict) -> None:
        cleaned_config = self.validate_proxyconfig(self.module, proxy_config)
        self.__proxy_config = cleaned_config