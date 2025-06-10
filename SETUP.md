# Server Setup

## [ipset & iptables]

### STEPS:
#### ipset
- Create ipset blacklist: `ipset create blacklist hash:ip family inet hashsize 1024 maxelem 65536`.
- Save current ipset rules: `ipset save > /etc/ipset.rules`. This dumps the blacklist definition into a file called `ipset.rules`.

#### iptables
- Configure iptables to drop traffic packets from IPs in the ipset blacklist: `iptables -I INPUT -m set --match-set blacklist src -j DROP`
- Sanity check, verify: `iptables -L -n --line-numbers`
- As in `ipset` above, save the current `iptables` rules like so: `iptables-save > /etc/iptables.rules`.

## [systemd]

### STEPS:
- Create the systemd service that will restore ipset based on the rules you just created, on reboot: `touch /etc/systemd/system/ipset-restore.service`
- `vim` into the file and create the service conditions:

####
[Unit]
Description=Restore ipset rules
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c '! /sbin/ipset list blacklist > /dev/null 2>&1 && /sbin/ipset restore < /etc/ipset.rules || echo "ipset already exists, skipping restore"'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
####

- As above, do the same for iptables to restore on reboot: `touch /etc/systemd/system/iptables-restore.service`. Then, `vim` into the file and create the service conditions:

####
[Unit]
Description=Restore iptables firewall rules
After=network.target

[Service]
Type=oneshot
ExecStart=/sbin/iptables-restore < /etc/iptables.rules
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
####

- Enable the services: `systemctl enable ipset-restore.service && systemctl enable iptables-restore.service`


## Setup Confirmation:
- Reboot your server
- Run the following: `ipset list` and `iptables -L -n`. You should still see the just-created blacklist, and the DROP rule.