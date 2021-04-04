#!/bin/bash
echo "he"
WAT=$1

echo "generint stuff"
wat2wasm --debug-names $WAT.wat -o $WAT.dbg.wasm && \
		wasm-objdump $WAT.dbg.wasm -h > $WAT.dbg.headers && \
		wasm-objdump $WAT.dbg.wasm -x > $WAT.dbg.details

		
