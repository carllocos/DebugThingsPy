from __future__ import annotations
from typing import Union, List

from utils import valid_addr, dbgprint, errprint
from web_assembly import WAModule, Expr
from things import ChangesHandler, DebugSession

class Debugger:
    def __init__(self, dev, wamodule = None):
        super().__init__()
        self.__device = dev
        self.__breakpoints = []
        self.__advance_ctr = 0

        self.__changeshandler = ChangesHandler(wamodule)
        self.__wamodule = wamodule
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

    def give_offset(self):
        return self.device.vm.get_offset()

    @property
    def breakpoints(self) -> List[Expr]:
        return self.__breakpoints

    @breakpoints.setter
    def breakpoints(self, nb: List[Expr]) -> None:
        self.__breakpoints = nb

    def ack_current_bp(self, bp):
        dbgprint(f'Debugger: ack current bp: {bp}')
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

    def run(self) -> None:
        self.__update_session()
        if self.device.run():
            dbgprint(f'device {self.device.name} is running')
        else:
            dbgprint(f'device {self.device.name} failed to run')

    def pause(self, code_info):
        print("received paused request")
        # state = State(self.__device, code_info)
        # _msgs = self.__serializer.run(state)
        # self.__medium.send(_msgs, self.__device)

    def step(self, amount = 1):
        self.__update_session()

        self.device.step(amount)
        _json = self.device.get_execution_state()
        _sess = DebugSession.from_json(_json, self.module, self.device)
        self.changes_handler.add(_sess)
        return _sess
        

    def ask_for_offset(self):
        self.device.ask_for_offset()

    def add_breakpoint(self, expr: Expr) -> None:
        if self.device.add_breakpoint(expr.addr, self.__atbreakpoint):
            dbgprint(f"breakpoint added at {expr}")
            self.breakpoints.append(expr.copy())
        else:
            dbgprint(f'failed to add breakpoint {expr}')

    def remove_breakpoint(self, inst: Expr) -> None:
        if self.device.remove_breakpoint(inst.addr):
            dbgprint(f'breakpoint {inst} removed')
            self.breakpoints = list(filter(lambda i: i.addr != inst.addr, self.breakpoints))
        else:
            dbgprint(f"could not remove breakpoint {inst}")

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

    def debug_session(self):
        _json = self.device.get_execution_state()
        _sess = DebugSession.from_json(_json, self.module, self.device)
        self.changes_handler.add(_sess)
        return _sess

    def receive_session(self, debugsess: DebugSession) -> None:
        if debugsess.modified:
            upd = debugsess.get_update()
            if not upd.valid:
                dbgprint("invalid change")
                return 
            self.changes_handler.add(upd)
        _json = debugsess.to_json()
        _json['breakpoints'] = [ hex(bp.addr) for bp in self.breakpoints]
        self.device.receive_session(_json)

    def add_proxyconfig(self, proxy_config: dict) -> None:
        cleaned_config = self.validate_proxyconfig(self.module, proxy_config)
        self.__proxy_config = cleaned_config

    #Callbacks
    def ack_add_bp(self, bp):
        dbgprint(f'Debugger: ack add bp: {bp}')
        self.__breakpoints.append(bp)

    def ack_rmv_bp(self, bp):
        dbgprint(f'Debugger: ack rmv bp: {bp}')
        self.__breakpoints = [p for p in self.__breakpoints if p != bp]

    #private methods
    def __atbreakpoint(self, bp: str) -> None:
        dbgprint(f"reached breakpoint {bp}")
        self.debug_session()

    def __update_session(self, debugsess: Union[DebugSession, None] = None) -> None:
        ds = self.changes_handler.session if debugsess is None else debugsess
        if ds is None:
            return

        if ds.modified:
            upd = debugsess.get_update()
            if not upd.valid:
                dbgprint("invalid change")
                return 
            debugsess.add(upd)
            #TODO other update
            self.receive_session(debugsess)