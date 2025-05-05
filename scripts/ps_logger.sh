#!/bin/bash

while true; do
    # -axo becomes -eo for linux
    ps -axo pid,ppid,user,%cpu,state,start,time,command | awk '{
        cmd = "date +\"%Y-%m-%d %H:%M:%S\""
        cmd | getline timestamp
        close(cmd)
        print timestamp "," $1 "," $2 "," $3 "," $4 "," $5 "," $6 "," $7 "," substr($8, 1, 100)
        fflush()
        }'
        echo "END"
        sleep 5
done
