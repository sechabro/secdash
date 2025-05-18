#!/bin/bash
ssh secdash-vps "grep 'Failed password' /var/log/auth.log | tail -n 20"
