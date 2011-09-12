#!/bin/bash

awk -f fix_indent.awk $1 > fixed_$1
mv -v fixed_$1 $1
