from __future__ import annotations
from typing import Union
import sys
import logging
import threading

from boards import load_device
from sockserver import EventSystem, run_server
from web_assembly import WAModule
from things import Debugger

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")

RemoteDevice: Union[None, Debugger] = None
LocDevice: Union[None, Debugger] = None


def compile_module(aModule: WAModule):
    aModule.compile(cache=True)


def on_config(config_file, connection):
    global RemoteDevice, LocDevice
    logging.info("Creating Remote VM")
    mod = WAModule.from_file(config_file["program"], out="./out/")

    tid = threading.Thread(target=compile_module, args=[mod])
    tid.start()
    config_file["name"] = "remote device"
    RemoteDevice = Debugger(load_device(config_file), mod)

    logging.info("Creating Local VM")
    local_config = {"name": "local device", "port": 8080}
    LocDevice = Debugger(load_device(local_config), mod)

    tid.join()
    connection.emit("initial config done")


def connect2VMs(_):
    global RemoteDevice, LocDevice
    logging.info("connecting to VMS")
    LocDevice.connect()
    LocDevice.upload_module(config=LocDevice.proxy_config)


# def catch_all(data):
#     logging.error("unhandled event data {}")
#     sys.exit(-1)


def register_handlers():
    event_handlers = EventSystem()
    event_handlers.on_event("initial config", on_config)
    event_handlers.on_event("connect to vms", connect2VMs)
    return event_handlers


if __name__ == "__main__":
    HOST, PORT = "localhost", 8192
    if len(sys.argv) == 2:
        PORT = int(sys.argv[1])
    logging.info(f"SocketServer {PORT}")
    run_server((HOST, PORT), register_handlers())
