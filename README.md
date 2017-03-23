### DSVR (Domain-Specific VPN Router)

**PURPOSE**

If you're using a VPN service today, you may have found the following limitations:  

1) All or nothing. Either ALL traffic goes down the VPN or none - unable to be selective.  
2) Only one VPN at a time. Cannot selectively route certain sites down one VPN, and others down another VPN.  
3) Unless you've configured your VPN at the router level, it's likely that only a single device can use your VPN at one time.  

This project serves to address each of the above - see the FEATURES section.  

Please review my blog post here http://darranboyd.wordpress.com/2013/07/05/selective-vpn-routing-solution-dsvr/  

**FEATURES**

![SCREENSHOT](https://raw.github.com/dboyd13/DSVR/master/screenshots/dsvr-logical-v0.2.png)
![SCREENSHOT](https://raw.github.com/dboyd13/DSVR/master/screenshots/dsvr-physical-v0.2.png)

1) Per-site VPN routing down specific VPN connections whilst all other traffic goes down the native internet connection, for example:  

    ussite1.com -> United States based PPTP VPN
    ussite2.com -> United States based PPTP VPN
    uksite1.com -> United Kingdom based PPTP VPN
    uksite2.com -> United Kingdom based PPTP VPN
    allothersites -> Native internet connection

2) Supports multiple concurrent PPTP connections  
3) Transparent in-line device - no configuration changes required on any other network components or clients  
4) User specified DNS server for per-site DNS queries, for privacy from your ISP.  
5) Stateful firewall (SPI)  
6) Port Forwarding & uPnP on existing router/AP not affected (see TODO)  
7) CLI access via SSH  
8) Web administration portal 

![SCREENSHOT](https://raw.github.com/dboyd13/DSVR/master/screenshots/webadmin.png)

**PRE-REQUISTES**

Existing:  
1) Separate Modem/CE device with ethernet and DHCP server  
2) Separate Router/AP to provide Wifi/Wired access to clients  
3) Minimum of one PPTP VPN account from a service provider. Else it'll just be a pass-through router/firewall.  

New components required:  
1) Raspberry Pi (Model B, 512mb RAM)  
2) SD Card (4gb min) flashed with Raspbian Wheezy  
3) Power source for Raspberry Pi  
4) USB NIC adapter (suggest Apple model: A1277)  
5) Standard Ethernet cable  

**KNOWN LIMITATIONS**

1) Theoretical 100mbit/s - likely less due to RPi using USB bus.  
2) Cannot perform source-based VPN routing without removal of existing NAT boundary, so that real sources can be determined. (see WIKI for workaround)
3) Currently assumes your LAN subnet is 192.168.1.0 (see TODO)  
4) Currently only support PPTP based VPNs (see TODO)  


**TESTED WITH**

1) Raspbian Wheezy (2012-12-16)  
2) StrongVPN PPTP VPN accounts  

**INSTALLATION**  

1) Flash your SD card with Raspbain (Wheezy 2012-12-16) http://downloads.raspberrypi.org/images/raspbian/2012-12-16-wheezy-raspbian/2012-12-16-wheezy-raspbian.zip  
2) Boot-up your RPi with the on-board NIC plugged into your network (without the USB NIC module installed), to obtain a DHCP address  
3) Determine the RPi IP address (hint: look at your router web interface), and SSH into it - ssh pi@ipaddress  
4) Run `sudo raspi-config`, expand_rootfs, change_pass, change_locale, change_timezone, boot behavior (desktop no). Reboot - yes  
5) SSH back into the RPi, then update apt - `sudo apt-get update && sudo apt-get install ca-certificates`  
6) Install GIT - `sudo apt-get install git`  
7) In case you're not already there, move to the home directory `cd ~/`  
8) Download DSVR from git - `git clone https://github.com/dboyd13/DSVR.git ./dsvr-source`  
9) `cd dsvr-source`  
10) Run the install script with sudo - `sudo ./installdsvrpackage.sh` - take note of any errors that may come up, note that the failure to start the ISC DHCP Server is expected and not an issue. This will take a while, as it will be installing a number of dependent packages via the web.  
11) Remove the "source" folder - `rm -r ~/dsvr-source`  
12) Issue the `sudo shutdown -h now` command to power-down the RPi  
13) With the power-off, plug the USB NIC into an available USB port.  
14) Wire your RPI inline between your existing Modem/CE and your existing Router/Access Point as follows:  

    eth0 (onboard) is 'internet side'
    eth1 (usb) is 'lan side'

```
                        eth (inside)      eth (wan)
                        DHCP Server       DHCP Client
      +-----+           +                 NAT (Hide)        +-----+
      | P   |           |                 +                 | I   |
      | U   |           |                 |                 | N   |
      | B I |           |                 |                 | T C |
      | L N |    +------+   +---------+   +------------+    | E L |
      | I T |<---+Modem/|<--+Raspberry|<--+Router/     |<---+ R I |
      | C E |    |CE    |   |Pi       |   |Access Point|    | N E |
      |   R |    +------+   +---------+   +------------+    | A N |
      |   N |               |         |                     | L T |
      |   E |               |         +                     |   S |
      |   T |               |         eth1 (usb)            |     |
      +-----+               |         10.254.254.254        +-----+
                            +         DHCP Server
               eth0 (onboard)         Web admin server
                  DHCP Client         SSH server
                   NAT (Hide)         VPN gateway
```
15) Power-up the RPi, whilst it's booting power-down and power-up both your Modem/CE and your Router/Access Point  
16) Wait a while for things to come up, I'd guess around 3-5mins  
17) On your Router/Access Point verify that the WAN interface has received a DHCP lease from the RPi, something in the 10.254.254.x range  
18) Verify that the internet is still working from your client machines. If not wait a while longer, else something has gone wrong.  
19) Verify you can ssh to your RPi - ssh pi@10.254.254.254, verify that the RPi can access the internet both via IP and DNS.  
20) Verify that you pass the ShieldsUp! (www.grc.com/shieldsup) 'All Service Ports' stealth test, this is to test the SPI firewall is functional.  

The device should be a functional pass-through router/firewall at this point, see the next section to setup per-site VPNs.  

**VPN CONFIGURATION**

1) Browse to http://10.254.254.254  
2) Click 'add' to add a PPTP VPN connection  
3) Input all fields (note that VPN server MUST be an IP address - see TODO), and specify which sites you want to be routed down this connection, suggest you include a unique 'ip address checker' (aruljohn.com, strongvpn.com) site for each - this will help in verifying it's functional  
4) Click 'update', then 'back'  
5) Repeat 2-4 for each required PPTP VPN.  
6) Reboot router  
7) Wait - maybe 3-5mins, then test that per-site VPN routing is functional. If you included a unique 'ip address checker' site for each connection, this is the best initial test.  

Should be working now. Enjoy.  

**TODO**

1) Short Term

    - 'DMZ' for inside interface to circumvent dbl-nat issues (e.g. uPnP, port forwarding, VPN server)  

       installdsvrpackage.sh  
	- Run/debug and fix.  
	- Add Y/N prompt to explain what needs to happen once it completes (wiring, IP to connect to, setup PPTP connections)  

	makedsvrpackage.sh  
	- create scripts to refresh files in installstubs/  
	- create VERSION file based on provided arg[0]  

	dsvr-webadmin.py  
	- Allow hostname OR IP address input/parsing/encoding for peer VPN server. - FIXED.
	- Read and display VERSION file  
	- Don't assume 'require-mppe-128' and allow user to specify PPTP encryption (or not)

	dsvr.py  
	- Read and display VERSION file  

2) Medium Term  

    - make webadmin look better on iPad webkit browser  
    - form input validation  
    - Authentication for webadmin  

3) Long Term  
	
    - Add support for OpenVPN  
    - Allow change from 10.254.254.254 inside default (remember dhcpd.conf and DNSRouter init changes needed too!)  
    - Installer to prompt user for variables such as - inside IP address, LAN segment, install location  
    - don't assume 192.168.1.0 is LAN segment for routes and iptables  

**CREDIT**

    Portions of code taken from the dnschef project (https://thesprawl.org/projects/dnschef/)
    
    Copyright (C) 2013 Peter Kacherginsky
    All rights Reserved

**LICENSE**

    DSVR (Domain Specific VPN Router)
    Copyright 2013 Darran Boyd
    
    dboyd13 [at @] gmail.com
    
    Licensed under the "Attribution-NonCommercial-ShareAlike" Vizsage
    Public License (the "License"). You may not use this file except
    in compliance with the License. Roughly speaking, non-commercial
    users may share and modify this code, but must give credit and 
    share improvements. However, for proper details please 
    read the full License, available at
        http://vizsage.com/license/Vizsage-License-BY-NC-SA.html 
    and the handy reference for understanding the full license at 
        http://vizsage.com/license/Vizsage-Deed-BY-NC-SA.html
    
    Unless required by applicable law or agreed to in writing, any
    software distributed under the License is distributed on an 
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, 
    either express or implied. See the License for the specific 
    language governing permissions and limitations under the License.

**LINKS**  

    - ASCII diagram (http://www.asciiflow.com/#Draw8450497916007412677/1697158644)
    - To properly calc memory usage due to disk caching - http://www.linuxatemyram.com/index.html
