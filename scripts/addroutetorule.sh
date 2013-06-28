#! /bin/sh
IP=$1
#Based on input (e.g. ppp0) output number (i.e. 0)
TABLENUM=`echo $2 | grep -o '[0-9]*'`
#Add one to value, as table numbers start from 1 (not 0)
TABLENUM=$(($TABLENUM + 1))

sudo ip rule add to $IP table $TABLENUM
