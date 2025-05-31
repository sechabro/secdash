#!/bin/bash

# for local testing:

#ssh secdash-vps "
#    while true; do
#        ps -eo pid,ppid,user,%cpu,state,start,time,command | awk '{
#            cmd = \"date +%Y-%m-%d_%H:%M:%S\"
#            cmd | getline timestamp
#            close(cmd)
#            if (NF >= 8) {
#                print timestamp \",\" \$1 \",\" \$2 \",\" \$3 \",\" \$4 \",\" \$5 \",\" \$6 \",\" \$7 \",\" substr(\$8, 1, 100)
#            }
#            
#            fflush()
#        }'
#        echo \"END\"
#        sleep 5
#    done
#"

# for VPS
# chmod +x ps_logger.sh <--- add permissions
# bash ./ps_logger.sh <--- test run it

while true; do
    ps -eo pid,ppid,user,%cpu,state,start,time,command | awk '
        {
            cmd = "date +%Y-%m-%d_%H:%M:%S"
            cmd | getline timestamp
            close(cmd)
            if (NF >= 8) {
                print timestamp "," $1 "," $2 "," $3 "," $4 "," $5 "," $6 "," $7 "," substr($8, 1, 100)
            }
            fflush()
        }
    '
    echo "END"
    sleep 5
done