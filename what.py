import serial as ser
import threading
import queue

from communication import medium
from communication import request as req

class Serial(medium.Medium):

    def __init__(self, serializer):
        super().__init__()
        self.__serial = False
        self.__requests =queue.Queue()
        self.__reqs_complete = queue.Queue()
        self.__worker = False
        self.__serializer = serializer

    #TODO make thread safe
    def __schedule_msgs(self, msgs):
        _reqs = [ req.Request(m) for m in msgs]
        for q in _reqs:
            self.__requests.put(q)
        return _reqs

    #TODO improve to wait on message instead of thread
    def wait_for_answers(self, requests):
        self.__worker.join()

    def send(self, msgs, dev):
        _reqs = self.__schedule_msgs(msgs)
        if self.__worker:
            return _reqs

        _ser =self.__serial
        _enc = self.__serializer
        _all_reqs = self.__requests
        _reqs_compl = self.__reqs_complete
        self.__worker = threading.Thread(target=send_read_data, args=(_ser, _enc, _all_reqs, _reqs_compl))
        self.__worker.start()
        return _reqs

    def start_connection(self, dev):
        sc = dev.get_serial_config()
        if sc is None:
            raise Exception("device config needed for ser.communication")

        port = sc.device
        b = sc.baudrate
        rt = sc.timeout
        wt = sc.write_timeout
        bs = ser.EIGHTBITS
        self.__serial = ser.Serial(port, baudrate=b, timeout=rt, write_timeout=wt, bytesize=bs)
        if not self.__serial.is_open:
            self.__serial.open()
        return self.__serial.is_open

    def close_connection(self, dev):
        if self.__serial:
           return self.__serial.close()
        return False

    def discover_devices(self):
        raise NotImplementedError

def read_data(serial, serializer, request):
    recv_msg = request.message.reply_template()
    answ = {'start': False, 'end': False}
    if recv_msg.has_start():
        print(f'reading start {recv_msg.start}')
        answ['start'] = serial.read_until(recv_msg.start)
    if recv_msg.has_end():
        print(f'reading until {recv_msg.end}')
        answ['end'] = serial.read_until(recv_msg.end)
    recv_msg.receive_answer(answ)
    request.mark_done()
    serializer.process_answer(request.message)

def send_read_data(serial, serializer, requests):
    print(f'serial scheduled to send f{requests.size()}')
    while not requests.empty():
        _req = requests.get()
        _msg = _req.message
        print(f'sending {_msg.payload}')
        self.__serial.write(_msg.payload)
        _req.mark_send()
        if not _msg.expects_reply:
            _req.mark_done()

    _req.mark_waiting()
    recv_msg = request.message.reply_template()
    answ = {'start': False, 'end': False}
    if recv_msg.has_start():
        print(f'reading start {recv_msg.start}')
        answ['start'] = serial.read_until(recv_msg.start)
    if recv_msg.has_end():
        print(f'reading until {recv_msg.end}')
        answ['end'] = serial.read_until(recv_msg.end)
    recv_msg.receive_answer(answ)
    request.mark_done()
    serializer.process_answer(request.message)

class SerialConfig:

    def __init__(self, **kwargs):
        args = ['name', 'device', 'baudrate', 'timeout', 'write_timeout']
        checks = [lambda n: type(n) is str,
                  lambda d: type(d) is str,
                  lambda b: type(b) is int,
                  lambda t: type(t) is float,
                  lambda t: type(t) is float,
                  lambda e: type(e) is bool]

        for f_idx, a in enumerate(args):
            if not kwargs[a]:
                raise ValueError(f'{a} arg missing')

            if not checks[ f_idx ](kwargs[a]):
                raise ValueError(f'{a} is of incorrect type')

        self.name = kwargs['name']
        self.device = kwargs['device']
        self.baudrate = kwargs['baudrate']
        self.timeout = kwargs['timeout']
        self.write_timeout = kwargs['write_timeout']

    @staticmethod
    def from_port_info(port_info):
        return SerialConfig(port_info)
#  def halt(dev):
#      dev.send_data(toAddr(dev, "HALT" ))

#  def pause(dev):
#      dev.send_data(toAddr(dev, "PAUSE" ))

#  def step(dev):
#      dev.send_data(toAddr(dev, "STEP" ))

#  def add_bp(dev, bp):
#      address = toAddr(dev, "BPAdd", bp )
#      dev.send_data(address)
#      return address

#  def remove_bp(dev, bp):
#      address = toAddr(dev, "BPRem", bp )
#      dev.send_data(address)
#      return address

#  def dump(dev):
#      dev.send_data(toAddr(dev, "DUMP"))

#  def dump_local(dev, qf = 1):
#      data = INTERUPT_TYPE['DUMPLocals']
#      #  if qf > 1: #TODO code should be correct. Implement as warduino side to process arguments
#      #      #  dev.send_data(toAddr(dev, "DUMPLocals", hex(qf)))
#      #      hx = hex(qf)[2:]
#      #      _size = math.floor(len(hx) / 2)
#      #      if _size % 2 != 0:
#      #          print("WARNING: added O in front for qf\n")
#      #          hx += '0'
#      #          _size +=1

#      #      _hex_siz = hex(_size)[2:]
#      #      if _size < 16:
#      #          _hex_siz = '0' + _hex_siz
#      #      data += _hex_siz + hx

#      data +='\n'
#      dev.send_data(data.upper().encode('ascii'))

#  def update_fun(dev):
#      dev.send_data(toAddr(dev, "UPDATEFun" ))

#  def update_local(dev):
#      dev.send_data(toAddr(dev, "UPDATELocal" ))



