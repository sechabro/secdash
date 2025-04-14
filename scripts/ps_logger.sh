#!/bin/bash

while true; do
    ps aux | awk '$3 > 0.1 {
        cmd = "date +\"%Y-%m-%d %H:%M:%S\""
        cmd | getline timestamp
        close(cmd)
        split(timestamp, dt, " ")
        date = dt[1]
        time = dt[2]
        print date "," time "," $1 "," $2 "," $3 "," $4 "," $5 "," $6 "," $7 "," $8 "," $9 "," $10 "," substr($11, 1, 100)
        fflush()
        }'
        echo "END"
        sleep 1
done
