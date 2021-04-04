#!/bin/bash

wat2wasm -v $1 > source_map.txt
grep @ -A1 source_map.txt > map_stripped.txt
sed -i -e 's/@//g' map_stripped.txt
sed -i -e '/--/d' map_stripped.txt
awk '{getline b;printf("%s %s\n",$0,b)}' map_stripped.txt > tmp && mv tmp map_stripped.txt
sed -i -e 's/ \}/, addr:/g' map_stripped.txt
sed -i -e 's/addr: /addr: 0x/g' map_stripped.txt
sed -i -e 's/\(.*\):\(.*\)/\1 }, /g' map_stripped.txt
sed -i -e '1s/^/\ source_map = [/' map_stripped.txt
sed -i -e '$ s/,.$/];/' map_stripped.txt
cat map_stripped.txt
