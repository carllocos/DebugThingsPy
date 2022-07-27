from __future__ import annotations

# from typing import Union, List, Any
from aiohttp import web
from . import wsgi_app
import eventlet
import socketio
import sys
import logging


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")
PORT = 8192

sio = socketio.AsyncServer()
app = socketio.WSGIApp(sio)
# 3app = socketio.Middleware(sio)
##app = web.Application()
##sio.attach(app)


@sio.event
def connect():
    logging.info("new client connected")
    print("Connecting")


@sio.on("*")
async def catch_all(event, sid, data):
    logging.info(f"caught event {event}")
    print(f"connect {event}")


# async def handle_client(reader, writer):
#     request = None
#     while request != "quit":
#         request = (await reader.read(255)).decode("utf8")
#         response = str(eval(request)) + "\n"
#         writer.write(response.encode("utf8"))
#         await writer.drain()
#     writer.close()


# async def run_server(port):
#     logging.info(f"Starting Server {port}")
#     io = socketio.AsyncServer()


# server = await asyncio.start_server(handle_client, "localhost", port)
# async with server:
#     await server.serve_forever()


if __name__ == "__main__":
    eventlet.wsgi.server(eventlet.listen(("", PORT)), app)
# 3   web.run_app(app)
# 3run_server(PORT)
# if len(sys.argv) <= 1:
# asyncio.run(run_server(PORT))
# else:
#     asyncio.run(run_server(int(sys.argv[1])))
