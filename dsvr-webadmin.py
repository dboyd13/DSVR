#!/usr/bin/env python
#
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

import re
import os
import sys
import commands
import configparser
import netifaces
from datetime import timedelta
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
app = Flask(__name__)

def getdsvrini(filename):
    if "/" not in filename:
        filename = os.path.abspath(os.path.dirname(sys.argv[0])) + "/" + filename
    config = configparser.ConfigParser()
    config.read(filename)
    return config

def writedsvrini(config,filename):
    if "/" not in filename:
        filename = os.path.abspath(os.path.dirname(sys.argv[0])) + "/" + filename
    file = open(filename,"w")
    config.write(file)
    file.close()

def getpeerdata():
    peers = commands.getstatusoutput('ls /etc/ppp/peers/db* -1 | xargs -n1 basename')
    ppppeers_dict = {}
    if peers[0] == 0:

        for peerfile in peers[1].split('\n'):
            contents = []
            filefullpath = "/etc/ppp/peers/" + peerfile
            file = open(filefullpath)
            while 1:
                line = file.readline().rstrip("\r\n")
                if not line:
                    break
                contents.append(line)
            ppppeers_dict[peerfile] = contents
    return ppppeers_dict

def writepeerfile(input_list, peerstr):
    filename = "/etc/ppp/peers/" + peerstr
    for index in input_list:
        if os.path.exists(filename):
            os.remove(filename)
        file = open(filename, 'w+')
        for listitem in input_list:
            file.write(listitem + "\n")
        file.close()
        
def delinitdscript(peerstr):
    filename = "/etc/init.d/" + peerstr
    if os.path.exists(filename):
        os.remove(filename)
        
def createinitdscript(peerstr):
    srcfilename = os.path.abspath(os.path.dirname(sys.argv[0])) + "/scripts/vpninitdtemplate"
    dstfilename = "/etc/init.d/" + peerstr
    if not os.path.exists(dstfilename):
        command = "sudo cp " + srcfilename + " " + dstfilename
        os.system(command)
        command = "sudo chmod +x " + dstfilename
        os.system(command)
        command = "update-rc.d " + peerstr + " defaults"
        os.system(command)

def encodepeerfile(input_dict, peerstr):
    plist = []
    plist.append("#friendlyname" + " " + str(input_dict[peerstr]['friendlyname']))
    plist.append("#interestingdomains" + " " + ",".join(input_dict[peerstr]['interestingdomains']))
    plist.append('pty "pptp ' + str(input_dict[peerstr]['vpnserver']) + ' --nolaunchpppd"')
    plist.append("name" + " " + str(input_dict[peerstr]['username']))
    plist.append("password" + " " + str(input_dict[peerstr]['password']))
    plist.append("unit"+ " " + str(re.findall(r'\d+', str(input_dict[peerstr]['interface']))[0]))
    plist.append("mtu" + " " + str(input_dict[peerstr]['mtu']))
    plist.append("mru" + " " + str(input_dict[peerstr]['mru']))
    plist.append("lcp-echo-failure" + " " + str(input_dict[peerstr]['lcp-echo-failure']))
    plist.append("lcp-echo-interval" + " " + str(input_dict[peerstr]['lcp-echo-interval']))
    plist.append("idle" + " " + str(input_dict[peerstr]['idle']))
    for option in input_dict[peerstr]['options']:
        plist.append(str(option))
    return plist

def parsepeerdata():
    my_dict = getpeerdata()
    peer_index = {}

    #Parse and display Peer Data
    for indexitem in my_dict:
        peer_options = []
        peer_detail = {}
        for listitem in my_dict[indexitem]:
            key = listitem.split(' ',1)
            if "#friendlyname" in key:
                peer_detail['friendlyname'] = listitem.split(' ',2)[1]
            if "#interestingdomains" in key:
                peer_detail['interestingdomains'] = listitem.split(' ',2)[1]
            elif "pty" in key:
                vpnserverstr = re.findall(r'[0-9]+(?:\.[0-9]+){3}', listitem)
                peer_detail['vpnserver'] = vpnserverstr
            elif "name" in key:
                peer_detail['username'] = listitem.split(' ',2)[1]
            elif "password" in key:
                peer_detail['password'] = listitem.split(' ',2)[1]
            elif "mtu" in key:
                peer_detail['mtu'] = listitem.split(' ',2)[1]
            elif "mru" in key:
                peer_detail['mru'] = listitem.split(' ',2)[1]
            elif "unit" in key:
                peer_detail['interface'] = "ppp" + listitem.split(' ',2)[1]
            elif "lcp-echo-failure" in key:
                peer_detail['lcp-echo-failure'] = listitem.split(' ',2)[1]
            elif "lcp-echo-interval" in key:
                peer_detail['lcp-echo-interval'] = listitem.split(' ',2)[1]
            elif "idle" in key:
                peer_detail['idle'] = listitem.split(' ',2)[1]
            else: #else these are not key value pairs, so must be otions
                peer_options.append(listitem)
        #peer_detail['interestingdomains'] = config[indexitem]['interestingdomains']
        peer_detail['options'] = peer_options
        peer_index[indexitem] = peer_detail
    return peer_index
    
def uptime():
 
     try:
         f = open( "/proc/uptime" )
         contents = f.read().split()
         f.close()
     except:
        return "Cannot open uptime file: /proc/uptime"
 
     total_seconds = float(contents[0])
 
     MINUTE  = 60
     HOUR    = MINUTE * 60
     DAY     = HOUR * 24
 
     days    = int( total_seconds / DAY )
     hours   = int( ( total_seconds % DAY ) / HOUR )
     minutes = int( ( total_seconds % HOUR ) / MINUTE )
     seconds = int( total_seconds % MINUTE )
 
     string = ""
     if days > 0:
         string += str(days) + (days == 1 and "day" or "days" ) + ", "
     if len(string) > 0 or hours > 0:
         string += str(hours) +  "h" + ", "
     if len(string) > 0 or minutes > 0:
         string += str(minutes) + "m" #+ ", "

     return string;

@app.route('/dsvrprocess', methods = ['POST'])
def dsvrprocess():
    if request.method == 'POST':
        allowedactions = ['start','stop','restart']
        action = str(request.form['action'])
        if action in allowedactions:
            command = "/etc/init.d/dsvr " + action + " &"
            os.system(command)
    return redirect(url_for('main')) 

@app.route('/modifypptp',methods = ['POST','GET'])
def modify_pptp():
    if request.method == 'POST':

        peer_file = str(request.form['peer'])
        unit = str(re.findall(r'\d+', request.form['peer']))

        updatepeer_details = {}
        updatepeer_index = {}
        updatepeer_options = []
        updatepeer_domainlist = []
        
        updatepeer_details['friendlyname'] = str(request.form['friendlyname'])
        updatepeer_details['vpnserver'] = str(request.form['vpnserver'])
        updatepeer_details['username'] = str(request.form['username'])
        updatepeer_details['password'] = str(request.form['password'])
        updatepeer_details['interface'] = str("ppp" + str(unit))
        updatepeer_details['mtu'] = str(request.form['mtu'])
        updatepeer_details['mru'] = str(request.form['mru'])
        updatepeer_details['lcp-echo-failure'] = str(request.form['lcp-echo-failure'])
        updatepeer_details['lcp-echo-interval'] = str(request.form['lcp-echo-interval'])
        updatepeer_details['idle'] = str(request.form['idle'])
        updatepeer_details['interestingdomains'] = []
        domainlist = [x.lower() for x in request.form.getlist("domainfield")]
        for domain in domainlist:
            if domain:
                updatepeer_details['interestingdomains'].append(domain)
        updatepeer_details['options'] = defaultpeeroptions
        updatepeer_index[peer_file] = updatepeer_details
        updatepeer_index[peer_file] = encodepeerfile(updatepeer_index, peer_file)
        writepeerfile(updatepeer_index[peer_file],peer_file)
        peer_data = parsepeerdata()
        return render_template('modifypptp.html',peerdata=peer_data,peerfile=peer_file)
    else:
        peer_data = parsepeerdata()
        peer_file = request.args.get('peer')
        return render_template('modifypptp.html',peerdata=peer_data,peerfile=peer_file)
    

@app.route('/delpptp',methods = ['POST','GET'])
def del_pptp(): 

    if request.method == 'POST':
        filename = "/etc/ppp/peers/" + str(request.form['peer'])
        if os.path.exists(filename):
            os.remove(filename)
            delinitdscript(str(request.form['peer']))
        return redirect(url_for('main'))        
    else:
        peer = str(request.args.get('peer'))
        return render_template('delpptp.html',peer=peer)

    
@app.route('/reboot',methods = ['POST','GET'])
def reboot(): 

    if request.method == 'POST':
        os.system('reboot')
        return redirect(url_for('main'))        
    else:
        return render_template('reboot.html')

        
    

@app.route('/addpptp',methods = ['POST','GET'])
def add_pptp():
    
    if request.method == 'POST':
        peer_data = parsepeerdata()

        #Find the first available interface number       
        existingintnum = []
        for index in peer_data:
            existingintnum.append(re.findall(r'\d+', str(peer_data[index]['interface'])))
        
        for num in range (0,10):
            if str(num) not in str(existingintnum):
               unit = num
               break

        #Create a new peer name
        peer_file = "db-ppp" + str(unit)

        newpeer_details = {}
        newpeer_index = {}
        newpeer_options = []
        
        newpeer_details['friendlyname'] = str(request.form['friendlyname'])
        newpeer_details['vpnserver'] = str(request.form['vpnserver'])
        newpeer_details['username'] = str(request.form['username'])
        newpeer_details['password'] = str(request.form['password'])
        newpeer_details['interface'] = str("ppp" + str(unit))
        newpeer_details['mtu'] = str(request.form['mtu'])
        newpeer_details['mru'] = str(request.form['mru'])
        newpeer_details['lcp-echo-failure'] = str(request.form['lcp-echo-failure'])
        newpeer_details['lcp-echo-interval'] = str(request.form['lcp-echo-interval'])
        newpeer_details['idle'] = str(request.form['idle'])
        newpeer_details['interestingdomains'] = []
        for domain in request.form.getlist("domainfield"):
          if domain:
              newpeer_details['interestingdomains'].append(domain)
        newpeer_details['options'] = defaultpeeroptions
        
        newpeer_index[peer_file] = newpeer_details
        newpeer_index[peer_file] = encodepeerfile(newpeer_index, peer_file)
        writepeerfile(newpeer_index[peer_file],peer_file)
        createinitdscript(peer_file)
        peer_data = parsepeerdata()
        return render_template('modifypptp.html',peerdata=peer_data,peerfile=peer_file)
    else:
        #peer_data = parsepeerdata()
        #usedinterfacenumbers = []
    
        #usedinterfacenumbers.append(re.findall(r'\d+', str(peer_data[index]['interface'])))
       
        return render_template('addpptp.html')

@app.route('/')
def main():
    ##Get and parse PPP peer data
    peer_data = parsepeerdata()

    #Get system uptime and format nicely
#    with open('/proc/uptime','r') as f:
#        uptime_seconds = float(f.readline().split()[0])
#        uptime_string = str(timedelta(seconds = uptime_seconds))
#        delay = timedelta(seconds = uptime_seconds)
#        if (delay.days > 0):
#            out = str(delay).replace(" days, ", ":")
#            out = str(delay).replace(" day, ", ":")
#        else:
#            out = "0:" + str(delay)
#        outAr = out.split(':')
#        outAr = ["%02d" % (int(float(x))) for x in outAr]
#        out   = ":".join(outAr)
#        uptime_string = str(out)

    uptime_string = uptime()

    #Testing updates INI file
    config = getdsvrini("dsvr.ini")
    
##    MEMORY
##    ------
##
##    % Available for apps etc - Linux will release mem from disk cache
##    free -m | awk '/Mem:/ { total=$2 } /buffers\/cache/ { used=$3 } END {print used/total*100}'
##
##    Total in MB
##    free -m | awk '/Mem:/ { total=$2 } END {print total}'
##    Used in MB
##    free -m | awk '/buffers\/cache/ { used=$3 } END {print used}'
##    Free in MB
##    free -m | awk '/buffers\/cache/ { free=$4 } END {print free}'
##
##    CPU
##    ---
##
##    CPU Load (5 min average)
##    uptime | awk '{print ($9)*100}'
##
##    CPU Load (15 min average)
##    uptime | awk '{print ($10)*100}'    
    
    #Determine CPU metric
    sysstats = []
    #CPU Load - 5 minute average
    #sysstats.append(commands.getstatusoutput("uptime | awk '{printf \"%.0f\",($9)}'"))
    #CPU Load - 15 minute average    
    #sysstats.append(commands.getstatusoutput("uptime | awk '{printf \"%.0f\",($10)}'"))
    sysstats.append(commands.getstatusoutput("top -n1 | awk '/Cpu\(s\):/ {print $2 + $4}'"))
    #Memory % Used
    sysstats.append(commands.getstatusoutput("free -m | awk '/Mem:/ { total=$2 } /buffers\/cache/ { used=$3 } END {printf \"%.0f\",used/total*100}'"))
    
    #Determine static IP interfaces - note this does check ppp interfaces, have to assume those are DHCP.
    staticints = []
    staticints  = commands.getstatusoutput("cat /etc/network/interfaces | grep 'inet static' | awk '{print $2}'")[1].split("\n")
    
    numofstaticroutes = {}
    
    for index in peer_data:
        unit = re.findall(r'\d+', str(peer_data[index]['interface']))[0]
        tablenum = int(unit) + 1
        numofstaticroutes[index] = commands.getstatusoutput("ip rule | grep 'lookup " + str(tablenum) + "' | wc -l")

    #Determine if the dsvr process is running
    dsvrstatus = 0
    if os.path.exists("/var/run/dsvr.pid"):
        pid = str(commands.getstatusoutput('cat /var/run/dsvr.pid')[1])
        psaxoutput = commands.getstatusoutput('ps ax | grep ' + pid + ' | grep -v grep')
        if 'dsvr' in psaxoutput[1]:
            dsvrstatus = 1

    return render_template('main.html',peerdata=peer_data,uptime=uptime_string,numofstaticroutes=numofstaticroutes,network=netifaces,config=config,dsvrstatus=dsvrstatus,sysstats=sysstats,staticints=staticints)

if __name__ == '__main__':
    defaultpeeroptions = ['lock','nodetach','noauth','refuse-eap','persist','require-mppe-128']
    app.run(host='0.0.0.0',debug=True,port=80)
