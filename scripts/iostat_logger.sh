#!/bin/bash

# for local testing:

#ssh secdash-vps "
#  iostat 1 | awk '
#    NR > 2 && \$1 > 0 && \$1 ~ /^[0-9.]+$/ {
#      cmd = \"date +%Y-%m-%d,%H:%M:%S\"
#      cmd | getline timestamp
#      close(cmd)
#      split(timestamp, dt, \",\")
#      date = dt[1]
#      time = dt[2]
#      print date \",\" time \",\" \$1 \",\" \$2 \",\" \$3 \",\" \$4 \",\" \$5 \",\" \$6
#    }
#  '
#"

# for VPS
# chmod +x iostat_logger.sh <--- add permissions
# bash ./iostat_logger.sh <--- test run it

iostat 1 | awk '
  NR > 2 && $1 > 0 && $1 ~ /^[0-9.]+$/ {
    cmd = "date +%Y-%m-%d,%H:%M:%S"
    cmd | getline timestamp
    close(cmd)
    split(timestamp, dt, ",")
    date = dt[1]
    time = dt[2]
    print date "," time "," $1 "," $2 "," $3 "," $4 "," $5 "," $6
  }
'