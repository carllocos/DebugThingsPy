from __future__ import annotations
from typing import Union
import threading

import typer

from utils import get_logger
from things import OOTConfig, Debugger, DebugSession
from servers import TCPServer
from communication import WOODProtocol
from web_assembly import WAModule
from eventsystem import EventSystem, EventEmitter
from boards import load_device

RemoteDevice = Debugger(None)
LocDevice = Debugger(None)
aModule = None
event_system = EventSystem()
app = typer.Typer()
DefaultConfig = OOTConfig.default_config()
cli_logger = get_logger("CLI")

# Helpers


def verify_missing_keys(keys: list[str], event: dict, em: EventEmitter) -> bool:
    for k in keys:
        try:
            event[k]
        except KeyError:
            event_system.logger.info(f"missing `{k}` key")
            em.emitt_error(f"missing `{k}` key")
            return False
    return True


def prepare_session_state(local_device: bool, session: DebugSession) -> dict:
    state = session.to_json()
    state["debugging_local"] = local_device
    state["version"] = session.version
    return state


def get_device_and_validate(event: dict, em: EventEmitter) -> tuple[bool, Debugger]:
    global LocDevice, RemoteDevice
    if event["debugging_local"] is None:
        em.emitt_error("missing `debugging_local` key")
        return (False, Debugger(None))
    dev = LocDevice if event["debugging_local"] else RemoteDevice
    return (True, dev)


def compile_module(aModule: WAModule):
    aModule.compile(cache=True)
    print(f"compilation done {aModule}")


# CALLBACKS
def on_disconnection():
    global RemoteDevice, LocDevice
    event_system.logger.info("Disconnecting from VMs")
    LocDevice.disconnect()
    # RemoteDevice.disconnect()


def on_config(config_file: dict, em: EventEmitter):
    global RemoteDevice, LocDevice, aModule
    event_system.logger.info("Creating Remote VM")
    if not verify_missing_keys(
        ["program", "ip_device", "port_device"], config_file, em
    ):
        return

    aModule = WAModule.from_file(config_file["program"], out="./out/")

    tid = threading.Thread(target=compile_module, args=[aModule])
    tid.start()
    remote_config = {
        "name": "remote device",
        "port": config_file["port_device"],
        "host": config_file["ip_device"],
    }
    # config_file["name"] = "remote device"
    RemoteDevice = Debugger(load_device(remote_config), aModule)
    register_device_handlers(RemoteDevice)

    event_system.logger.info("Creating Local VM")
    local_config = {
        "name": "local device",
        "port": 8167,
        "host": "localhost",
    }
    LocDevice = Debugger(load_device(local_config), aModule)
    proxy_config = {
        "port": config_file.get("port_device", 80),
        "proxy": config_file.get("proxy", []),
        "host": config_file["ip_device"],
    }

    try:
        cleaned = LocDevice.validate_proxyconfig(aModule, proxy_config)
        LocDevice.add_proxyconfig(cleaned)
        policy = config_file.get("breakpoint_policy", "default")
        if not LocDevice.validat_bp_policy(policy):
            event_system.logger.info(f"invalid breakpoint_policy ginve: `{policy}`")
            raise ValueError(f"invalid breakpoint_policy ginve: `{policy}`")

        event_system.logger.info(f"using breakpoint-policy: `{policy}`")
        register_device_handlers(LocDevice)
        tid.join()
        em.emit("initial config done")
    except ValueError as e:
        event_system.logger.info(f"ValueError {e}")
        em.emitt_error(str(e))


def on_connect2VMs(event, em: EventEmitter):
    global RemoteDevice, LocDevice, aModule
    if aModule is not None:
        event_system.logger.info("connecting to VMS")
        # event_system.logger.info(
        #     f"connecting to remote VM {RemoteDevice.device.host} {RemoteDevice.device.port}"
        # )
        # if not RemoteDevice.connect():
        #     event_system.logger.error("connecting to remote VM failed")
        #     return em.emitt_error("connection to remote device")

        event_system.logger.info("connecting to Local VM")
        event_system.logger.info(f"connecting to local VM port {LocDevice.device.port}")
        LocDevice.connect()
        LocDevice.upload_module(aModule)
        LocDevice.upload_proxies()

        for bp in event.get("breakpoints", []):
            try:
                LocDevice.add_breakpoint(bp["linenr"])
            except ValueError as e:
                event_system.logger.error(f"failed to add_breakpoint: `{e}`")

        session: DebugSession = LocDevice.debug_session()
        state = prepare_session_state(local_device=True, session=session)
        event_system.logger.info(f"Emitting new state for `{LocDevice.name}`")
        event_system.logger.debug(f"PC of `{LocDevice.name}` {session.pc}")
        return em.emit("new state", state)

    event_system.logger.error("VMs connection cancelled due to missing info")
    err_reason = "no local device set" if LocDevice is None else "no program set"

    reason = f"configuration incomplete: `{err_reason}`"
    em.emitt_error(reason)


def on_step(event: dict, em: EventEmitter):
    global RemoteDevice, LocDevice
    _, dev = get_device_and_validate(event, em)
    dev.step()
    session = dev.session
    state = prepare_session_state(local_device=True, session=session)
    event_system.logger.info(f"Emitting new state for `{dev.name}`")
    event_system.logger.debug(f"PC of `{dev.name}` {session.pc}")
    em.emit("step done", state)


def on_run(event: dict, em: EventEmitter):
    valid, dev = get_device_and_validate(event, em)
    if not valid:
        return
    dev.run()
    em.emit("run ack", {"debugging_local": event["debugging_local"]})


def on_pause(event: dict, em: EventEmitter):
    valid, dev = get_device_and_validate(event, em)
    if not valid:
        return
    dev.pause()
    session = dev.session
    if session is None:
        event_system.logger.error("Session is None after pause")
        em.emitt_error("session None after pause")
        return
    event_system.logger.info(f"Emitting new state after pause for `{dev.name}`")
    local_device = event["debugging_local"]
    state = prepare_session_state(local_device, session)
    em.emit("paused", {"state": state})


def toggle_breakpoints(event: dict, em: EventEmitter):
    valid, dev = get_device_and_validate(event, em)
    if not valid:
        return

    event_system.logger.info(f"toggle breakpoints: {event['breakpoints']}")
    placed_bps = set([(bp.addr, bp.linenr) for bp in dev.breakpoints])
    new_bps = set([(int(bp["addr"], 16), bp["linenr"]) for bp in event["breakpoints"]])
    to_remove = placed_bps.difference(new_bps)
    to_add = new_bps.difference(placed_bps)
    event_system.logger.debug(f"current bps: {placed_bps}")
    event_system.logger.debug(f"new_bps: {new_bps}")
    event_system.logger.debug(f"to_remove: {to_remove}")
    event_system.logger.debug(f"to_add: {to_add}")
    for addr, linenr in to_remove:
        loc = hex(addr) if addr != 0 else linenr
        try:
            dev.remove_breakpoint(loc)
        except ValueError as e:
            event_system.logger.error(f"remove_breakpoint failed: {e}")

    for addr, linenr in to_add:
        loc = hex(addr) if addr != 0 else linenr
        try:
            dev.add_breakpoint(loc)
        except ValueError as e:
            event_system.logger.error(f"add_breakpoint failed: {e}")

    current_bps = [bp.to_dict() for bp in dev.breakpoints]
    data = {"debugging_local": event["debugging_local"], "breakpoints": current_bps}
    em.emit("toggled", data)


def on_bp_reached(dev: Debugger) -> None:
    global LocDevice, RemoteDevice
    if dev is LocDevice:
        session = LocDevice.debug_session()
        state = prepare_session_state(local_device=True, session=session)
        event_system.logger.info(f"Emitting new state for `{LocDevice.name}`")
        event_system.logger.debug(f"PC of `{LocDevice.name}` {session.pc}")
        return event_system.emit("bp reached", state)

    else:
        event_system.logger.info("apply out-of-place")


def on_proxies(event: dict, em: EventEmitter) -> None:
    global LocDevice
    LocDevice.upload_proxies(event["proxy"])
    event_system.logger.info(f"Proxy List updated to {event['proxy']}")
    em.emit("proxies updated")


def on_update_value(event: dict, em: EventEmitter) -> None:
    valid, dev = get_device_and_validate(event, em)
    event_name_done = "value updated"
    if not valid:
        return
    if not verify_missing_keys(["index", "value"], event, em):
        return

    try:
        stack_idx = event["index"]
        value = event["value"]
        if dev.session is None:
            response = {"succesful": False, "reason": "session is empty"}
            em.emit(event_name_done, response)
            return
        sv = dev.session.stack[stack_idx]
        sv.value = value
        bps = [
            hex(bp.addr) for bp in dev.breakpoints
        ]  # TODO remove adding breakpoints and fix bps in session
        event_system.logger.debug(f"bps {bps}")
        dev.receive_session(dev.session)
        for bp in bps:
            dev.add_breakpoint(bp)
        session = dev.session
        state = prepare_session_state(local_device=True, session=session)
        em.emit(event_name_done, {"succesful": True, "state": state})
    except IndexError:
        event_system.logger.info("out of range stack value")
        response = {"succesful": False, "reason": "unexisting index"}
        em.emit(event_name_done, response)


def on_update_module(event: dict, em: EventEmitter) -> None:
    valid, dev = get_device_and_validate(event, em)
    if not valid:
        return

    mod = WAModule.from_file(dev.module.filepath)
    dev.upload_module(mod)
    event_name_done = "module updated"
    is_local = event["debugging_local"]
    data = {"succesful": True, "debugging_local": is_local}
    if is_local:
        session = dev.debug_session()
        state = prepare_session_state(local_device=True, session=session)
        data["state"] = state
    em.emit(event_name_done, data)


def register_handlers():
    event_system.logger.info("registering handlers")
    event_handlers = EventSystem()
    event_handlers.on_event("initial config", on_config)
    event_handlers.on_event("connect to vms", on_connect2VMs)
    event_handlers.on_event("step", on_step)
    event_handlers.on_event("toggle breakpoints", toggle_breakpoints)
    event_handlers.on_event("run", on_run)
    event_handlers.on_event("disconnection", on_disconnection)
    event_handlers.on_event("update proxies", on_proxies)
    event_handlers.on_event("update value", on_update_value)
    event_handlers.on_event("pause", on_pause)
    event_handlers.on_event("update module", on_update_module)

    return event_handlers


def register_device_handlers(dbg: Debugger) -> None:
    event_system.logger.info(f"register handlers on `{dbg.name}`VM")
    dbg.on_event("at bp", on_bp_reached)


@app.command()
def startserver(port: Union[int, None] = None, config_path: Union[str, None] = None):
    config = DefaultConfig
    if port is not None:
        config.port = port
    elif config_path is not None:
        config = OOTConfig.from_json_file(config_path)
    else:
        cli_logger.info("starting TCPServer with default config")
    es = register_handlers()
    WOODProtocol.update_eventsystem(es)
    _server = TCPServer(config.port)
    _server.run(WOODProtocol)


if __name__ == "__main__":
    app()
