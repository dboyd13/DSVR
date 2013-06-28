#!/bin/sh
# DSVR (Domain Specific VPN Router)
# Copyright 2013 Darran Boyd
#
# Licensed under the "Attribution-NonCommercial-ShareAlike" Vizsage
# Public License (the "License"). You may not use this file except
# in compliance with the License. Roughly speaking, non-commercial
# users may share and modify this code, but must give credit and 
# share improvements. However, for proper details please 
# read the full License, available at
#     http://vizsage.com/license/Vizsage-License-BY-NC-SA.html 
# and the handy reference for understanding the full license at 
#     http://vizsage.com/license/Vizsage-Deed-BY-NC-SA.html
#
# Unless required by applicable law or agreed to in writing, any
# software distributed under the License is distributed on an 
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, 
# either express or implied. See the License for the specific 
# language governing permissions and limitations under the License.

#Customize start
BASEDIR="/home/$SUDO_USER/"
APPDIR="${BASEDIR}dsvr/"
WORKINGDIR=$PWD
#Customize end

#Check if running as ROOT or SUDO, else exit.
if [ $(id -u) -ne 0 ]; then
    echo "[*Error*] Please run with SUDO, or as ROOT user"
    exit
fi

echo "[INFO] Working directory: $WORKINGDIR"
echo "[INFO] Base directory: $BASEDIR"
echo "[INFO] dsvr directory: $APPDIR"

#Check if see nothing else its at our desired directory
if [ -d "$APPDIR" ]; then
   echo "[*Error*] ${APPDIR} directory already exists"
   exit
fi

#Check for internet access
echo "[INFO] Checking for internet access, required for package installs"
if ping -W 5 -c 1 google.com >/dev/null; then
    echo "[INFO] Internet access appears to be fine"
else
    echo "[*Error*] Cannot access the internet"
    exit
fi

#######################################
echo "[INFO] Installing required packages"

apt-get update -q=1
apt-get install ca-certificates -q=1 -y

echo "[INFO] Installing isc-dhcp-server"
apt-get install isc-dhcp-server -q=1 -y

echo "[INFO] Installing pptp-linux"
apt-get install pptp-linux -q=1 -y

echo "[INFO] Installing python-pip"
apt-get install python-pip -q=1 -y

echo "[INFO] Installing python-dev"
apt-get install python-dev -q=1 -y

echo "[INFO] Installing flask"
pip install flask

echo "[INFO] Installing configparser"
pip install configparser

echo "[INFO] Installing netifaces"
pip install netifaces

echo "[INFO] Installing tldextract"
pip install tldextract

echo "[INFO] Completed installing required packages"
#######################################

echo "[INFO] Configuring packages and network"

#Append the required DHCP config
cat ./installstubs/dhcpdstub.conf | tee -a /etc/dhcp/dhcpd.conf

cp ./installstubs/interfaces /etc/network/interfaces

#Uncomment the ip forward by removing the #
sed -i 's/#net.ipv4.ip_forward/net.ipv4.ip_forward/g' /etc/sysctl.conf

cp ./installstubs/db-restarteth0 /etc/init.d/db-restarteth0
chmod +x /etc/init.d/db-restarteth0
update-rc.d db-restarteth0 defaults

cp ./installstubs/iptables.up.rules /etc/iptables.up.rules

cp ./installstubs/iptables /etc/network/if-pre-up.d/iptables
chown root:root /etc/network/if-pre-up.d/iptables
chmod +x /etc/network/if-pre-up.d/iptables
chmod 755 /etc/network/if-pre-up.d/iptables

cp ./installstubs/db-policyroute /etc/ppp/ip-up.d/db-policyroute
chmod +x /etc/ppp/ip-up.d/db-policyroute

#######################################

echo "[INFO] Installing dsvr in $APPDIR"

cp -r ./ $APPDIR

cp ./installstubs/dsvr /etc/init.d/dsvr
sed -i "s,/replacemewithsed/,${APPDIR},g" /etc/init.d/dsvr
chmod +x /etc/init.d/dsvr
update-rc.d dsvr defaults

cp ./installstubs/dsvr-webadmin /etc/init.d/dsvr-webadmin
sed -i "s,/replacemewithsed/,${APPDIR},g" /etc/init.d/dsvr-webadmin
chmod +x /etc/init.d/dsvr-webadmin
update-rc.d dsvr-webadmin defaults

echo "[INFO] Completed installing dsvr in ${APPDIR}"
echo ""
echo "Complete. Please reboot (sudo reboot) and connect via 10.254.254.254"
echo ""
