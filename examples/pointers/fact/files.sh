#!/bin/bash

NAME=$1

echo cleaning
rm $NAME.wasm $NAME.wast $NAME.wasm.dbg

echo $NAME.C to WASM
emcc $NAME.c -s SIDE_MODULE=1 -g4 --ignore-dynamic-linking -s WASM=1 -O3 -s NO_FILESYSTEM=1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -o $NAME.wasm
# emcc $NAME.c -s STANDALONE_WASM --ignore-dynamic-linking -s WASM=1 -O3 -s NO_FILESYSTEM=1  -o $NAME.wasm
# emcc -s WASM=1 -s SIDE_MODULE=1 -O2 $NAME.c -o $NAME.wasm #one that worked
# emcc -s WASM=1 -O2 $NAME.c -o $NAME.wasm
# emcc $NAME.c -o $NAME.js -s WASM=1

echo WASM2WAST
wasm2wat $NAME.wasm >> $NAME.wast

echo WAST2WASM for dbg
wat2wasm -v $NAME.wast >> $NAME.wasm.dbg

echo CREATING IMPORT FILE
xxd -i $NAME.wasm > import.c
echo "/*" >> import.c
echo $NAME.wasm.dbg >> import.c
echo "*/" >> import.c
