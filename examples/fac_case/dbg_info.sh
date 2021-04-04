#!/bin/bash
WAT=$1

../../debuggingthings/c_libs/wabt/build/./wat2wasm --debug-names -v $WAT.wat -o $WAT.dbg.wasm > $WAT.dbg.verbose.txt && \
		wasm-objdump $WAT.dbg.wasm -h > $WAT.dbg.headers && \
		wasm-objdump $WAT.dbg.wasm -x > $WAT.dbg.details

		
