#!/bin/sh

if [ -z "$1" ]; then
	echo "Please specify version number e.g. 0.1a"
	exit
fi

mkdir ~/dsvr-v$1
cp -r ./* ~/dsvr-v$1
cd ~/
tar -cvzf dsvr-$1.tar.gz dsvr-v$1
rm -r ~/dsvr-v$1/
