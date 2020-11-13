from communication import protocol as ptc

class Interact:
    def __init__(self, dev, serializer, medium):
        super().__init__()
        self.__device = dev
        self.__serializer = serializer
        self.__medium = medium

    def intialize(self, code_info):
        if not self.start_connection():
            print('connection failed to start')
            return

        state = State(self.__device, code_info)
        _msgs = self.__serializer.initialize_step(state)
        _reqs = self.__medium.send(_msgs, self.__device)
        self.__medium.wait_for_answers(_reqs)

    def start_connection(self):
        return self.__medium.start_connection(self.__device)

    def halt(self, code_info):
        print('received halt request')
        state = State(self.__device, code_info)
        _msgs = self.__serializer.halt(state)
        print(f'received msgs {_msgs}')
        self.__medium.send(_msgs, self.__device)

    def run(self, code_info):
        print('received run request')
        state = State(self.__device, code_info)
        _msgs = self.__serializer.run(state)
        self.__medium.send(_msgs, self.__device)

    def pause(self, code_info):
        state = State(self.__device, code_info)
        _msgs = self.__serializer.run(state)
        self.__medium.send(_msgs, self.__device)

    def step(self, code_info):
        state = State(self.__device, code_info)
        _msgs = self.__serializer.run(state)
        self.__medium.send(_msgs, self.__device)

    def add_breakpoint(self, code_info):
        state = State(self.__device, code_info)
        _msgs = self.__serializer.add_breakpoint(state)
        _reqs = self.__medium.send(_msgs, self.__device)
        self.__medium.wait_for_answers(_reqs)


    def remove_breakpoint(self, code_info):
        state = State(self.__device, code_info)
        _msgs = self.__serializer.remove_breakpoint(state)
        self.__medium.send(_msgs, self.__device)

    def update_fun(self, code_info):
        pass

    def get_callstack(self,code_info):
        state = State(self.__device, code_info)
        _msgs = self.__serializer.callstack_msgs(state)
        _reqs = self.__medium.send(_msgs, self.__device)
        self.__medium.wait_for_answers(_reqs)
        return self.__serializer.get_callstack()

    #FOR DEBUG
    def get_med(self):
        return self.__medium
    def get_encoder(self):
        return self.__serializer

    def get_serial(self):
        return self.__medium.get_serial()

    def test_add_bp(self, addr):
        return self.add_breakpoint(BreakPoint(addr))

    def test_rmv_bp(self, addr):
        return self.remove_breakpoint(BreakPoint(addr))

class State:

    def __init__(self, dev, code_info):
        self.__dev = dev
        self.__code_info = code_info

    def device(self):
        return self.__dev

    def code_info(self):
        return self.__code_info


class BreakPoint:

    def __init__(self, addr):
        self.__addr = addr


    def hex_addr(self):
        return self.__addr
#  class CallStack:
#      def __init__(self, frames):
#          self.__frames = frames
#          self.__idx=0

#      def peek(self):
#          return self.__frames[self.__idx]

#      def next(self):
#          if self.__idx >= len(self.__frames):
#              return False
#          i = self.__idx
#          self.__idx += 1
#          return self.__frames[i]

#      def reset(self):
#          self.__idx = 0


#  class ReqQueue:

#      def __init__(self):
#          super().__init__()
#          self.__queue = []

#      def add_req(self, req):
#          self.__queue.push(req)


#      def hasReq(self):
#          return len(self.__queue) > 0




#  def read_data(dev):
#      __all_msgs = set()
#      __is_dump = False
#      __is_local= False
#      while True:
#          b = dev.get_serial().read_until(bytes([ord('\n')]))
#          msg = b.decode('utf-8')
#          if len(msg) > 0:
#              if __is_dump or __is_local:
#                  try:
#                      if __is_dump:
#                          dev.setDump(json.loads(msg), json.loads(msg))
#                          __is_dump = False
#                      if __is_local:
#                          dev.setDumpLocal(json.loads(msg))
#                          #  dev.setDumpLocal(json.loads(msg[:len(msg) -2]))
#                          __is_local = False
#                  except:
#                      print(msg)
#              else:
#                  print(msg)

#              if msg.find(__special)>=0:
#                  __is_dump = True
#              if msg.find(__special2)>=0:
#                  __is_local = True

    #  def enable_listening(self, verbose = False):
    #      if self.__serial is None:
    #          raise TypeError('connect first, invoke method connect on device')
    #      if self.__listener is None:
    #          #  print(f'creating the thread! verbose {verbose}')
    #          self.__listener = threading.Thread(target=read_data, args=(self,))
    #          self.__verbose = verbose
    #          self.__listener.start()


    #  def setOffset(self, off):
    #      self.__offset = off

    #  def getOffset(self):
    #      return self.__offset

    #  def setDump(self, d, org):
    #      self.__offset = d['start'][0]
    #      self.__originalDump = org
    #      self.__dump = d

    #      #start bytes
    #      int_offs = hex2Int(self.__offset)
    #      d['start']= ['0x0']

    #      #setting pc
    #      d['pc'] = hex(hex2Int(d['pc']) - int_offs)

    #      #settings breakpoints
    #      d['breakpoints'] = [hex(hex2Int(bp) - int_offs) for bp in d['breakpoints']]

    #      #settings functions
    #      for f in d['functions']:
    #          f['from'] = hex(hex2Int(f['from']) - int_offs)
    #          f['to'] = hex(hex2Int(f['to']) - int_offs)

    #      #settings callstack
    #      for cs in d['callstack']:
    #          if (cs['ra'] == '0x0') and (cs['fp'] == -1):
    #              continue
    #          cs['ra'] = hex(hex2Int(cs['ra']) - int_offs)


    #  def orgDump(self):
    #      return self.__originalDump

    #  def dump(self):
    #      return self.__dump

    #  def setDumpLocal(self, localDump):
    #      self.__localDump = localDump

    #  def dump_local(self):
    #      return self.__localDump

    #  def getStack(self):
    #      vals = self.__localDump
    #      return CallStack(vals['frames'])

    #  def breakpoints(self):
    #      if self.__dump:
    #          return self.__dump['breakpoints']
    #      return []



