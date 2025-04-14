#!/bin/bash

iostat 1 | awk '
  NR > 2 && $1 > 0 && $1 ~ /^[0-9.]+$/ {
    cmd = "date +\"%Y-%m-%d %H:%M:%S\""
    cmd | getline timestamp
    close(cmd)
    split(timestamp, dt, " ")
    date = dt[1]
    time = dt[2]
    print date "," time "," $1 "," $2 "," $3 "," $4 "," $5 "," $6 "," $7
  }
'