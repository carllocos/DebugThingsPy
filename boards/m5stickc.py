from communication import serial as ser
from . import warduino

class M5StickC:


    @staticmethod
    def serialConfig():
        c = {
            'name': 'ttyUSB0',
            'device': '/dev/ttyUSB0',
            'baudrate': 115200,
            'timeout': float(5),
            'write_timeout': float(5),
            'exclusive': True
        }
        return ser.SerialConfig(**c)


    @staticmethod
    def serializer():
        return warduino.Serializer()





#  class DUMP(ptc.AMessageTemplate):

#      def start(self):
#          return "DUMP_START\n"

#      def end(self):
#          return "DUMP_END\n"

#  class DUMP_STACK_VALS(ptc.AProtocol):

#      def start(self):
#          return "STACK_START\n"

#      def end(self):
#          return "STACK_END\n"


#  #API WARDUINO see file interrupt_operations.cpp

#  def sum_hexs(off, ad):
#      int_offs = int(off[2:], 16)
#      int_ad = int(ad[2:], 16)
#      return hex(int_offs + int_ad)

#  def rmv_off(dev, adr):
#      int_offs = int(dev.getOffset()[2:], 16)
#      int_ad = int(adr[2:], 16)
#      return hex(int_ad - int_offs)


#  INTERUPT_TYPE = {
#    "RUN" : '01',
#    "HALT" : '02',
#    "PAUSE" : '03',
#    "STEP" : '04',
#    "BPAdd" : '06',
#    "BPRem" : '07',
#    "DUMP" : '10',
#    "DUMPLocals" : '11',
#    "UPDATEFun" : '20',
#    "UPDATELocal" : '21'
#  }


#  def toAddr(dev, interupt_type, d=''):
#      r = INTERUPT_TYPE[interupt_type]
#      if len(d)>0:
#          hx = sum_hexs(dev.getOffset(), d)[2:] #remove 0x
#          _size = math.floor(len(hx) / 2)
#          if _size % 2 != 0:
#              print("WARNING: toAddr not even addr\n")

#          _hex_siz = hex(_size)[2:]
#          if _size < 16:
#              _hex_siz = '0' + _hex_siz
#          r = r + _hex_siz + hx

#      r +='\n'
#      return r.upper().encode('ascii')

#  def run(dev):
#      dev.send_data(toAddr(dev, "RUN" ))

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





