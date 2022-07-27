from web_assembly import WAModule
import threading

from eventsystem import EventSystem, EventEmitter
from boards import load_device
from things import Debugger

RemoteDevice = None
LocDevice = None
aModule = None
event_system = EventSystem()


def compile_module(aModule: WAModule):
    aModule.compile(cache=True)


def on_config(config_file: dict, connection):
    global RemoteDevice, LocDevice, aModule
    event_system.logger.info("Creating Remote VM")
    aModule = WAModule.from_file(config_file["program"], out="./out/")

    tid = threading.Thread(target=compile_module, args=[aModule])
    tid.start()
    config_file["name"] = "remote device"
    RemoteDevice = Debugger(load_device(config_file), aModule)

    event_system.logger.info("Creating Local VM")
    local_config = {"name": "local device", "port": 8080}
    LocDevice = Debugger(load_device(local_config), aModule)

    tid.join()
    connection.emit("initial config done")


def connect2VMs(_, em: EventEmitter):
    global RemoteDevice, LocDevice, aModule
    if LocDevice is not None and aModule is not None:
        event_system.logger.info("connecting to VMS")
        LocDevice.connect()
        LocDevice.upload_module(aModule, config=LocDevice.proxy_config)
        return

    event_system.logger.error("VMs connection cancelled due to missing info")
    err_reason = "no local device set" if LocDevice is None else "no program set"

    reason = f"configuration incomplete: `{err_reason}`"
    em.emitt_error(reason)


def register_handlers():
    event_system.logger.info("registering handlers")
    event_handlers = EventSystem()
    event_handlers.on_event("initial config", on_config)
    event_handlers.on_event("connect to vms", connect2VMs)
    return event_handlers


register_handlers()
