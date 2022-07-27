from __future__ import annotations
import logging
from os import EX_DATAERR
from typing import Union, List, Dict

from utils import valid_addr, dbgprint, errprint, infoprint
from utils import get_logger
from web_assembly import WAModule, Expr
from things import ChangesHandler, DebugSession

import time

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")

# FIXME if needed reconnect silently to disconnected device


class Debugger:
    Logger = get_logger("DBG")

    def __init__(self, dev, wamodule=None):
        super().__init__()
        self.__device = dev
        self.__breakpoints = []
        self.__changeshandler = ChangesHandler(wamodule)
        self.__wamodule = wamodule
        self.__proxy_config = None
        if dev is not None:
            dev.debugger = self
        self.__policies = []
        self.__handlers = {}

        # temporaty
        self.__bench = ""

    @property
    def name(self) -> str:
        return self.__device.name

    def bench_name(self, n: str) -> None:
        self.__bench = n

    def disconnect(self):
        self.device.disconnect()

    def on_event(self, event_name, cb) -> None:
        Debugger.Logger.info(f"add cb for `{event_name}` in `{self.name}`")
        self.__handlers[event_name] = cb

    def register_measure(self, tstart, tend, sess):
        import os

        len_callstack = len(sess.callstack.all_frames)
        len_vals = len(sess.stack)
        dtime = tend - tstart
        total_bytes = sess.total_size
        print(
            f"time:{dtime} callstack:{len_callstack} stack:{len_vals} total_bytes:{total_bytes}\n"
        )
        if self.__bench != "":
            f = open(self.__bench, "a")

            st = os.stat(self.__bench)
            if st.st_size == 0:
                f.write("time,callstack,stack,total_bytes\n")

            f.write(f"{dtime},{len_callstack},{len_vals},{total_bytes}\n")
            f.close()

    @property
    def proxy_config(self) -> Dict:
        return self.__proxy_config

    @property
    def session(self) -> Union[None, DebugSession]:
        return self.changes_handler.session

    @property
    def changes_handler(self) -> ChangesHandler:
        return self.__changeshandler

    @property
    def device(self):
        return self.__device

    @property
    def policies(self) -> List[str]:
        return self.__policies

    @policies.setter
    def policies(self, p: List[str]) -> None:
        self.__policies = p

    @property
    def module(self) -> WAModule:
        return self.__wamodule

    @module.setter
    def module(self, mod: WAModule) -> WAModule:
        self.__wamodule = mod

    @property
    def breakpoints(self) -> List[Expr]:
        return self.__breakpoints

    @breakpoints.setter
    def breakpoints(self, nb: List[Expr]) -> None:
        self.__breakpoints = nb

    def connect(self):
        c = self.device.connect(self.__handle_event)
        if not c:
            Debugger.Logger.info(f"connection failed to `{self.device.name}`")
        else:
            Debugger.Logger.info(f"connected to `{self.device.name}`")
        # pc = self.__proxy_config
        # if pc is not None and len(pc.get("proxy", [])) > 0:
        #     if upload_proxies:
        #         self.device.send_proxies(pc)

        # if self.device.is_local:
        #     pass
        #     # self.commit()

    def reconnect(self):
        if self.device.connect():
            dbgprint(f"connected to `{self.device.name}`")
        else:
            dbgprint(f"reconnection attempt failed to `{self.device.name}`")

    def halt(self, code_info):
        print("received halt request")
        # state = State(self.__device, code_info)
        # _msgs = self.__serializer.halt(state)
        # print(f'received msgs {_msgs}')
        # self.__medium.send(_msgs, self.__device)

    def run(self) -> None:
        if not self.device.connected:
            dbgprint(f"First connect to {self.device.name}")
            return
        self.__update_session()  # TODO uncomment
        if self.device.run():
            infoprint(f"`{self.device.name}` is running")
        else:
            dbgprint(f"device {self.device.name} failed to run")

    def pause(self) -> None:
        # TODO ask for debug session
        if not self.device.connected:
            dbgprint(f"First connect to {self.device.name}")
            return
        if self.device.pause():
            infoprint(f"`{self.device.name}` is paused")
        else:
            dbgprint(f"device {self.device.name} failed to pause")

    def step(self, amount: int = 1) -> DebugSession:
        if not self.device.connected:
            dbgprint(f"First connect to {self.device.name}")
            return

        self.__update_session()
        if self.device.step(amount):
            _json = self.device.get_execution_state()
            _sess = DebugSession.from_json(_json, self.module, self.device)
            self.changes_handler.add(_sess)
            infoprint("stepped")
            return _sess

    def step_over(self, expr: Union[Expr, DebugSession, None] = None) -> DebugSession:
        if not self.device.connected:
            dbgprint(f"First connect to {self.device.name}")
            return

        self.__update_session()  # TODO activate
        if expr is None:
            expr = self.changes_handler.session.pc
        elif isinstance(expr, DebugSession):
            expr = expr.pc

        if expr.exp_type not in ["call", "loop", "block", "if", "else"]:
            dbgprint("doing regular step")
            return self.step()

        end = None
        if expr.exp_type == "call":
            end = expr.code.next_instr(expr)
        else:
            end = expr.code.end_expr(expr)

        dbgprint(f"end instruction of {expr} is {end}")
        if not self.device.step_until(end.addr):
            dbgprint(f"could not stepover {expr}")

        dbgprint(f"stepped until {end}")
        _json = self.device.get_execution_state()
        _sess = DebugSession.from_json(_json, self.module, self.device)
        self.changes_handler.add(_sess)
        return _sess

    def add_breakpoint(self, expr: Union[Expr, int, str]) -> None:
        if not self.device.connected:
            Debugger.Logger.info(f"First connect to `{self.device.name}`")
            return
        if isinstance(expr, int) or isinstance(expr, str):
            expr = self.__get_instruction(expr)

        if self.device.add_breakpoint(expr.addr):
            Debugger.Logger.info(f"added breakpoint `{expr}`")
            self.breakpoints.append(expr.copy())
        else:
            Debugger.Logger.info(f"failed to add breakpoint `{expr}`")

    def __get_instruction(self, inst: Union[str, int]) -> Expr:
        if isinstance(inst, str):
            _expression = self.module.addr(inst)
            if _expression is None:
                raise ValueError(f"No expression at address `{inst}`")
            return _expression
        else:
            exps = self.module.linenr(inst)
            if len(exps) == 0:
                raise ValueError(f"No expression at line `{inst}`")
            return exps[0]

    def remove_breakpoint(self, inst: Union[Expr, str, int]) -> None:
        if not self.device.connected:
            Debugger.Logger.info(f"First connect to `{self.device.name}`")
            return
        if isinstance(inst, int) or isinstance(inst, str):
            inst = self.__get_instruction(inst)

        if self.device.remove_breakpoint(inst.addr):
            Debugger.Logger.info(f"removed breakpoint {inst}")
            self.breakpoints = list(
                filter(lambda i: i.addr != inst.addr, self.breakpoints)
            )
        else:
            infoprint(f"could not remove breakpoint {inst}")

    def update_fun(self, code_info):
        pass

    def upload_module(self, mod: Union[WAModule, None] = None):
        if not self.device.connected:
            Debugger.Logger.info(f"First connect to `{self.device.name}`")
            return

        wasm = None
        if mod is not None:
            wasm = mod.compile()
            self.module = mod
            self.__changeshandler.module = mod
        else:
            wasm = self.__changeshandler.commit()
        if self.device.commit(wasm):
            Debugger.Logger.info(f"Module Updated for `{self.name}`")

    def validat_bp_policy(self, policy) -> bool:
        return policy in ["default", "single-stop", "remove-and-proceed"]

    def validate_proxyconfig(self, mod: WAModule, config: dict) -> dict:
        cleaned_config = {"proxy": [], "host": None, "port": None}
        if config.get("proxy", False):
            cleaned_config["proxy"] = mod.make_proxy_config(config["proxy"])

        if config.get("host", False):
            if not valid_addr(config["host"]):
                raise ValueError(
                    f"configuration error: invalid host address `{config.get('host')}`"
                )
            cleaned_config["host"] = config["host"]
        if config.get("port", False):
            port = config["port"]
            if not isinstance(port, int) or port <= 0:
                raise ValueError(
                    f"configuration error: configured an incorrect port number for proxy requests"
                )
            cleaned_config["port"] = port

        return cleaned_config

    def upload_proxies(
        self, proxy: Union[None, dict, List[Union[str, int]]] = None
    ) -> None:
        if not self.device.connected:
            Debugger.Logger.info(f"First connect to `{self.device.name}`")
            return

        cleaned = {}
        if proxy is None:
            proxy = self.__proxy_config
        if isinstance(proxy, dict):
            cleaned = self.validate_proxyconfig(self.module, proxy)
        elif isinstance(proxy, list):
            config = {}
            config["host"] = self.__proxy_config["host"]
            config["port"] = self.__proxy_config["port"]
            config["proxy"] = proxy
            cleaned = self.validate_proxyconfig(self.module, config)
        self.device.send_proxies(cleaned)
        self.__proxy_config = cleaned

        # def upload_module(self, mod: WAModule) -> None:
        # config: Union[dict, None] = None,
        # proxy: Union[List[str], None] = None,
        # if config is None and proxy is None:
        #     return self.commit(mod)

        # if config is None:
        #     config = {}
        #     config["host"] = self.__proxy_config["host"]
        #     config["port"] = self.__proxy_config["port"]
        #     config["proxy"] = [] if proxy is None else proxy
        # cleaned_config = self.validate_proxyconfig(mod, config)

    #         if not self.device.connected:
    #             logging.info(f"First connect to {self.device.name}")
    #             return

    #         wasm = mod.compile()
    #         self.device.commit(wasm)
    # self.device.upload(wasm, cleaned_config)
    # self.__proxy_config = cleaned_config
    # infoprint("Upload Module Done")
    # infoprint(f"Functions to Proxy {[] if proxy is None else proxy}")
    # self.device.update_offset()
    # self.module = mod

    def debug_session(self) -> Union[DebugSession, None]:
        if not self.device.connected:
            dbgprint(f"First connect to {self.device.name}")
            return
        # starttime = time.monotonic()
        _json = self.device.get_execution_state()
        _sess = DebugSession.from_json(_json, self.module, self.device)
        # end2 = time.monotonic()
        # self.register_measure(starttime, end2, _sess)
        # s = f"time:{end2 - starttime},callstack:{len(_sess.callstack.all_frames)},stack:{len(_sess.stack)}\n"
        # print(s)
        # f = open(self.__bench , "a")
        # f.write(s)
        # f.close()

        self.changes_handler.add(_sess)
        return _sess

    def restore_session(self, version_nr: int) -> Union[DebugSession, None]:
        sess = self.__changeshandler.version(version_nr)
        if sess is not None:
            self.receive_session(sess)
        return sess

    def receive_session(self, debugsess: DebugSession) -> None:
        if not self.device.connected:
            dbgprint(f"First connect to {self.device.name}")
            return

        if debugsess.modified:
            infoprint("Debug Session Modified")
            upd = debugsess.get_update()
            if not upd.valid:
                dbgprint("invalid change")
                return
            self.changes_handler.add(upd)
            debugsess = upd

        _json = debugsess.to_dict()
        # print(f'the session to send breakpoints {_json["breakpoints"]}')
        _bps = _json["breakpoints"]
        for bp in self.breakpoints:
            _bps.append(hex(bp.addr))
        _json["breakpoints"] = _bps
        dbgprint(f"sending breakpoints {_json['breakpoints']}")
        if self.device.receive_session(_json):
            infoprint(f"`{self.device.name}` received debug session")
            self.debug_session()

    def add_proxyconfig(self, proxy_config: dict) -> None:
        cleaned_config = self.validate_proxyconfig(self.module, proxy_config)
        self.__proxy_config = cleaned_config

    # private methods
    def __handle_event(self, event: dict) -> None:
        ev = event["event"]
        cb = self.__handlers.get(ev)
        if ev == "at bp":
            Debugger.Logger.info(
                f"reached breakpoint {self.module.addr(event['breakpoint'])}"
            )
            self.__reachedbp = True
            self.debug_session()
            if "single-stop" in self.policies:
                Debugger.Logger.info(f"enforcing `single-stop' to `{self.device.name}`")
                for bp in self.breakpoints:
                    self.remove_breakpoint(bp)
                self.run()
            elif "remove-and-proceed" in self.policies:
                Debugger.Logger.info(
                    f"enforcing `remove-and-proceed` policy to `{self.device.name}`"
                )
                expr = self.module.addr(event["breakpoint"])
                Debugger.Logger.debug(f"breakpoint {expr}")
                self.remove_breakpoint(expr)
                self.run()
            if cb is not None:
                cb(self)

        elif ev == "disconnection":
            Debugger.Logger.info(f"device {self.device.name} disconnected")
            if cb is not None:
                cb()

        elif ev == "error":
            Debugger.Logger.info(f"error occured at `{self.device.name}`")
            _sess = DebugSession.from_json(
                event["execution_state"], self.module, self.device
            )
            _sess.exception = event["msg"]
            # end = event['time'].monotonic()
            # self.register_measure(event['start_time'], end, _sess)
            self.changes_handler.add(_sess)
        else:
            Debugger.Logger.error("not understood event occurred")

    def __update_session(self, debugsess: Union[DebugSession, None] = None) -> None:
        ds = self.changes_handler.session if debugsess is None else debugsess
        if ds is None:
            return

        if ds.modified:
            upd = ds.get_update()
            if not upd.valid:
                dbgprint("invalid change")
                return
            self.changes_handler.add(upd)
            # TODO other update
            self.receive_session(upd)
