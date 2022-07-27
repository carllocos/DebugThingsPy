# Arduino Socket Platform

PORT = /dev/ttyUSB0
FQBN = esp32:esp32:esp32wrover

compile: Arduino-socket.ino
	arduino-cli -v compile --fqbn $(FQBN) Arduino-socket.ino


flash: 
	arduino-cli upload -p $(PORT)  --fqbn $(FQBN) Arduino-socket.ino

monitor: 
	arduino-cli monitor -p $(PORT)  -c baudrate=115200
