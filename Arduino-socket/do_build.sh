#!/bin/bash

echo building for ESP32

PORT=/dev/cu.usbserial-2952919DA8
FQBN=esp32:esp32:esp32doit-devkit-v1:UploadSpeed=115200
make compile PORT=$PORT FQBN=$FQBN && make flash PORT=$PORT FQBN=$FQBN && make monitor PORT=$PORT

