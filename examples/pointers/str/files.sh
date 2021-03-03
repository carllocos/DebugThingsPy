#!/bin/bash

NAME=$1

echo cleaning
rm $NAME.wasm $NAME.wast $NAME.wasm.dbg import.c

echo $NAME.C to WASM
emcc -s WASM=1 -s SIDE_MODULE=1 -O2 $NAME.c -o $NAME.wasm
# emcc -s WASM=1 -O2 $NAME.c -o $NAME.wasm
# emcc $NAME.c -o $NAME.js -s WASM=1

echo WASM2WAST
wasm2wat $NAME.wasm >> $NAME.wast

echo WAST2WASM for dbg
wat2wasm -v $NAME.wast >> $NAME.wasm.dbg

echo CREATING IMPORT FILE
xxd -i $NAME.wasm > import.c
echo "/*" >> import.c
cat $NAME.wasm.dbg >> import.c
echo "*/" >> import.c
