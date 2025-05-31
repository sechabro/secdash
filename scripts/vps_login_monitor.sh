#!/bin/bash
# for local testing:

#ssh secdash-vps "
#    while true; do
#        grep 'Failed password' /var/log/auth.log | 
#        tail -n 20 | 
#        awk '
#        # Handle repeated message lines
#        {
#            if (\$5 == \"repeated\") {
#                if (\$12 == \"invalid\") {
#                    
#                    user = \$14
#                    ip_address = \$16
#
#                } else {
#                    user = \$12
#                    ip_address = \$14
#                }
#                
#                msg = \"\"
#                for (i = 9; i <= NF; i++) {
#                    msg = msg \$i \" \"
#                
#                }
#                #print \"below is a repeated message\"
#
#            } else if (\$7 == \"invalid\") {
#                user = \$9
#                ip_address = \$11
#
#                msg = \"\"
#                for (i = 4; i <= NF; i++) {
#                    msg = msg \$i \" \"
#                }
#
#            } else {
#                user = \$7
#                ip_address = \$9
#
#                msg = \"\"
#                for (i = 4; i <= NF; i++) {
#                    msg = msg \$i \" \"
#                }
#            }
#
#            gsub(/\] ?$/, \"\", msg)
#            print \$1 \",\" ip_address \",\" user \",\" msg
#        }'
#        
#        echo 'END'
#        sleep 10
#    done
#    "


# for VPS
# chmod +x vps_login_monitor.sh <--- add permissions
# bash ./vps_login_monitor.sh <--- test run it

while true; do
    grep 'Failed password' /var/log/auth.log | tail -n 20 | awk '
        {
            if ($5 == "repeated") {
                if ($12 == "invalid") {
                    user = $14
                    ip_address = $16
                } else {
                    user = $12
                    ip_address = $14
                }

                msg = ""
                for (i = 9; i <= NF; i++) {
                    msg = msg $i " "
                }

            } else if ($7 == "invalid") {
                user = $9
                ip_address = $11

                msg = ""
                for (i = 4; i <= NF; i++) {
                    msg = msg $i " "
                }

            } else {
                user = $7
                ip_address = $9

                msg = ""
                for (i = 4; i <= NF; i++) {
                    msg = msg $i " "
                }
            }

            gsub(/\] ?$/, "", msg)
            print $1 "," ip_address "," user "," msg
        }
    '
    echo "END"
    sleep 10
done