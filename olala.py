import select
import serial as ser
import socket               

def connect_to_port():
    sock = socket.socket()
    host = "192.168.1.3"  #ESP32 IP in local network
    port = 80

    sock.connect((host, port))
    return sock

if __name__ == "__main__":
    aSerial = ser.Serial(port='/dev/ttyUSB0', baudrate=115200, timeout=float(0.2), write_timeout=float(5))
    if not aSerial.is_open:
        aSerial.open()
    wait1 = b'waiting request'
    wait1_done = False
    wait2 = b'waiting request 1'
    sock = None

    attempts = 0
    while True:
        r = aSerial.readline()
        if b'Connected to the WiFi network' in r:
            break
        else:
            print(f"attempts {attempts}")
            attempts +=1 
            if attempts > 0: 
                break
    print("Connectiong..")
    sock = connect_to_port()
    evsock = connect_to_port()

    print("Connected")
    data = b""       
    evdata = b''
    #  sendCtr = 50
    quantityreceived = 10
    while True:
        rs, _, _ = select.select([sock, evsock], [], [], 3)

        for s in rs:
            data = s.recv(1024)
            lendata = len(data)
            which =  f'socket:' if s == sock else f'event:'
            print(f'{which}: #{lendata} {data}')
            print()

        #  evdata = evsock.recv(1024)
        #  lenev = len(evdata)
        #  if lenev> 0:
        #      print(f'event: #{lenev} {evdata}')
        #      print()
        #  #  if sendCtr == 0:
        #  #      sock.send(b'hey oh!!!')
        #  #      sendCtr = 50
        #  #  else:
        #  #      sendCtr -=1

        r = aSerial.readline()
        lr= len(r)
        if lr> 0:
            print(f'SERIAL: #{lr} {r}')
            print()

        #  if quantityreceived > 0:
        #      if quantityreceived == 7:
        #          evsock.close()
        #      elif quantityreceived == 4:
        #          sock.close()
        #      elif quantityreceived ==1:
        #          evsock = connect_to_port()

        #      quantityreceived -=1
        #  else:
        #      sock = connect_to_port()
        #      quantityreceived = 10
    
    evsock.close()
    sock.close()

