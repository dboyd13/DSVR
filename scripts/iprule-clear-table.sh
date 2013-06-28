#!/bin/sh

if [ -z "$1" ]
  then
  echo "no table name supplied"
else
 ip rule | grep "lookup $1" | cut -d: -f1 >tmp.txt
 for line in `cat tmp.txt`;do 
   ip rule del prio $line
 done
 rm tmp.txt
fi
