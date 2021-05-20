#!/bin/bash

HEAD=$1
FILENAME=decr
CFN=decr.c

max_ctr=63
ctr=0

prev_arg=-1
arg=1

while [ $ctr -le $max_ctr ]
do
  if [ $arg -le -0 ]
  then
    echo //$FILENAME=9223372036854775808  >> $CFN
  else
    echo //$FILENAME=$arg  >> $CFN
  fi
  ./generate_wast.py $prev_arg $arg $FILENAME.wast && \
    wat2wasm $FILENAME.wast -o $FILENAME.wasm && \
    xxd -i $FILENAME.wasm >> $FILENAME.c
    echo >> $CFN
  ((prev_arg=arg))
  ((arg*=2))
  ((ctr+=1))
done
rm $FILENAME.wasm
./generate_wast.py $prev_arg -1 $FILENAME.wast
exit 0