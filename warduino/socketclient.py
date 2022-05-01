import socket
import json

HOST = "192.168.204.153"  # The server's hostname or IP address
PORT = 8081  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print(f"Connecting to {HOST} {PORT}")
    s.connect((HOST, PORT))
    print("connected")
    while True:
        data = s.recv(1024)
        if data == b'':
            print("connection closed")
            break
        print(f"Received {data}")
        print(f"JSON: {json.loads(data.decode())}")
