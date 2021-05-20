#!/bin/python3.8

from tempfile import mkstemp
from shutil import move, copymode
from os import fdopen
import sys


def clean_arg(a):
    a = int(a)
    if a < -1:
        return a * -1
    return a

prev_arg = clean_arg(sys.argv[1])
new_arg = clean_arg(sys.argv[2])

old_content=f'(i64.const {prev_arg});;replace'
new_content= f'(i64.const {new_arg});;replace'
print(old_content)
print(new_content)

file_path = sys.argv[3]
print(file_path)

tmp_file , abs_path = mkstemp()
with fdopen(tmp_file ,'w') as new_file:
    with open(file_path,'r') as old_file:
        for line in old_file:
            new_file.write(line.replace(old_content, new_content))
            
copymode(file_path, abs_path)
move(abs_path, file_path)