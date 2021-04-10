from __future__ import annotations

import threading
import queue
import serial as ser

class MCUSerial:

    def __init__(self, config):
        self.__config = config
        self.__serial = False
        self.__requests =queue.Queue()
        self.__reqs_complete = queue.Queue()
        self.__worker = False
        self.__serializer = None

    #TODO remove
    @property
    def is_socket(self)-> bool:
        return False

    def get_worker(self):
        return self.__worker
    def get_serial(self):
        return self.__serial

    def set_serialize(self, s):
        self.__serializer = s

    #TODO make thread safe
    def __schedule_msgs(self, msgs):
        for m in msgs:
            self.__requests.put(m)
        return msgs
        # _reqs = [ req.Request(m) for m in msgs]
        # for q in _reqs:
        #     self.__requests.put(q)
        # return _reqs

    #TODO improve to wait on message instead of thread
    #TODO remove completed requests
    def wait_for_answers(self, requests):
        self.__worker.join()

    def send(self, msgs, dev):
        _reqs = self.__schedule_msgs(msgs)
        #TODO FIx bad interleave 
        if self.__worker and self.__worker.is_alive():
            print("WORKER BUSY")
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


def send_read_data(serial, serializer, requests, complete_queue):
    #print(f'serial scheduled to send #{requests.qsize()} reqs')
    while not requests.empty():
        #TODO fix bad interleave
        _req = requests.get()
        _msg = _req.message

        #print(f'send {_msg.NAME} payload: {_msg.payload}')
        if _msg.is_to_send():
            serial.write(_msg.payload)
        _req.mark_send()

        #TODO ugly ugly ugly!
        _req.mark_waiting()
        recv_msg = _msg.reply_template
        while recv_msg:
            answ = {'start': False, 'end': False}
            if recv_msg.has_start():
                #print(f'read start {recv_msg.start}')
                answ['start'] = serial.read_until(recv_msg.start)
                #print(f'the start {answ["start"]}')
            if recv_msg.has_end():
                #print(f'read until {recv_msg.end}')
                answ['end'] = serial.read_until(recv_msg.end)
                #print(f'the end {answ["end"]}')

            recv_msg.receive_answer(answ)
            serializer.process_answer(recv_msg)

            recv_msg = recv_msg.reply_template

        #  print('THREAD DONE')
        _req.mark_done()
        complete_queue.put(_req)