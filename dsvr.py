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
#
# Portions of code from the work of Peter Kacherginsky's dnschef - http://thesprawl.org/projects/dnschef/:
# iphelix [at] thesprawl.org.
#
# Copyright (C) 2013 Peter Kacherginsky
# All rights reserved.
#

from optparse import OptionParser,OptionGroup
from ConfigParser import ConfigParser
from lib.dnslib import *
from lib.IPy import IP

import threading, random, operator, time
import SocketServer, socket, sys, os, re
import tldextract,commands
import binascii

class DNSHandler():
           
    def parse(self,data):
        response = ""
    
        try:
            # Parse data as DNS        
            d = DNSRecord.parse(data)

        except Exception, e:
            print "[%s] %s: ERROR: %s" % (time.strftime("%H:%M:%S"), self.client_address[0], "invalid DNS request")

        # Proxy the request
        else:  
            extracted = tldextract.extract(str(d.q.qname))
            if 'addinterestingdomain-' in extracted.subdomain:
                addtointerface = extracted.subdomain.split('-',2)[1]
                domaintoadd = extracted.domain + "." + extracted.tld
                if domaintoadd not in interestingdomainsng[addtointerface]:
                    interestingdomainsng[addtointerface].append(domaintoadd)
                    print "[DB-I] Temporary added %s to interesting domains (until reboot/service restart), via %s" % (domaintoadd,addtointerface)
                else:
                    print "[DB-I] Ignoring request to add %s to interesting domains, already exists" % (domaintoadd)
            if isInterestingDomain(interestingdomainsng,str(d.q.qname))[0] == 1:
                nameserver_tuple = random.choice(db_dns_vpn_server).split('#')
            else:                                
                nameserver_tuple = random.choice(self.server.nameservers).split('#')
                
            response = self.proxyrequest(data,*nameserver_tuple)

            d = DNSRecord.parse(response)

            for item in d.rr:
                try: socket.inet_aton(str(item.rdata))
                except: 
                    isInteresting = []
                    isInteresting = isInterestingDomain(interestingdomainsng,str(d.q.qname))
                    if isInteresting[0] == 1:
                        interestingdomainsng[isInteresting[1]].append(str(item.rdata))
                else:
                    isInteresting = []
                    isInteresting = isInterestingDomain(interestingdomainsng,str(d.q.qname))
                    if isInteresting[0] == 1:
                        item.ttl=int(db_ttl_override_value) #TTL overide
                        if str(item.rdata) in existingroutes:
                            if options.verbose:    
                                print "[DB-I] %s | %s | %s | R~" % (str(d.q.qname),item.rdata,item.ttl) #DB Route exists, do nothing ("R~")
                        else:
                            if options.verbose:
                                print "[DB-I] %s | %s | %s | R+" % (str(d.q.qname),item.rdata,item.ttl) #DB Adding route ("R+")
                            interface=str(isInteresting[1])
                            existingroutes.append(str(item.rdata))
                            command = "sudo " + os.path.abspath(os.path.dirname(sys.argv[0])) + "/scripts/addroutetorule.sh " + str(item.rdata) + " " + str(interface)
                            os.system(command)
                    else:
                        if options.verbose:
                            print "[DB] %s | %s | %s | NR" % (str(d.q.qname),item.rdata,item.ttl) #DB No modifications ("NR")
            response = d.pack()

        return response         
    

    # Find appropriate ip address to use for a queried name. The function can 
    def findnametodns(self,qname,nametodns):
    
        # Split and reverse qname into components for matching.
        qnamelist = qname.split('.')
        qnamelist.reverse()
    
        # HACK: It is important to search the nametodns dictionary before iterating it so that
        # global matching ['*.*.*.*.*.*.*.*.*.*'] will match last. Use sorting for that.
        for domain,host in sorted(nametodns.iteritems(), key=operator.itemgetter(1)):
            domain = domain.split('.')
            domain.reverse()
            
            # Compare domains in reverse.
            for a,b in map(None,qnamelist,domain):
                if a != b and b != "*":
                    break
            else:
                # Could be a real IP or False if we are doing reverse matching with 'truedomains'
                return host
        else:
            return False
    
    # Obtain a response from a real DNS server.
    def proxyrequest(self, request, host, port="53"):
        reply = None
        try:
            if self.server.ipv6:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            sock.settimeout(3.0)

            # Send the proxy request to a randomly chosen DNS server
            sock.sendto(request, (host, int(port)))
            reply = sock.recv(1024)
            sock.close()

        except Exception, e:
            print "[!] Could not proxy request: %s" % e
        else:
	 return reply 

# UDP DNS Handler for incoming requests
class UDPHandler(DNSHandler, SocketServer.BaseRequestHandler):

    def handle(self):
        (data,socket) = self.request
        response = self.parse(data)
        
        if response:
            socket.sendto(response, self.client_address)

# TCP DNS Handler for incoming requests            
class TCPHandler(DNSHandler, SocketServer.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)
        
        # Remove the addition "length" parameter used in
        # TCP DNS protocol
        data = data[2:] 
        response = self.parse(data)
        
        if response:
            # Calculate and add the additional "length" parameter
            # used in TCP DNS protocol 
            length = binascii.unhexlify("%04x" % len(response))            
            self.request.sendall(length+response)            

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):

    # Override SocketServer.UDPServer to add extra parameters
    def __init__(self, server_address, RequestHandlerClass, nametodns, nameservers, ipv6):
        self.nametodns  = nametodns
        self.nameservers = nameservers
        self.ipv6        = ipv6
        self.address_family = socket.AF_INET6 if self.ipv6 else socket.AF_INET

        SocketServer.UDPServer.__init__(self,server_address,RequestHandlerClass) 

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    
    # Override default value
    allow_reuse_address = True

    # Override SocketServer.TCPServer to add extra parameters
    def __init__(self, server_address, RequestHandlerClass, nametodns, nameservers, ipv6):
        self.nametodns  = nametodns
        self.nameservers = nameservers
        self.ipv6        = ipv6
        self.address_family = socket.AF_INET6 if self.ipv6 else socket.AF_INET

        SocketServer.TCPServer.__init__(self,server_address,RequestHandlerClass) 

def isInterestingDomain(input_dict, searchstr):
    for index in input_dict:
        for item in input_dict[index]:
            if item in searchstr:
                list = [1,index]
                return list
    list = [0]
    return list

   
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
     
# Initialize and start dsvr        
def start_cooking(interface, nametodns, nameservers, tcp=False, ipv6=False, port="53"):
    try:
        if tcp:
            print "[*] dsvr is running in TCP mode"
            server = ThreadedTCPServer((interface, int(port)), TCPHandler, nametodns, nameservers, ipv6)
        else:
            server = ThreadedUDPServer((interface, int(port)), UDPHandler, nametodns, nameservers, ipv6)

        # Start a thread with the server -- that thread will then start one
        # more threads for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        
        # Loop in the main thread
        while True: time.sleep(100)

    except (KeyboardInterrupt, SystemExit):
        server.shutdown()
        print "[*] dsvr is shutting down."
        sys.exit()
    
if __name__ == "__main__":

    header  = "##########################################\n"
    header += "#              dsvr v0.1                 #\n"
    header += "#                  darranboyd.com        #\n"
    header += "##########################################\n"
    

    # Parse command line arguments
    parser = OptionParser(usage = "dsvr.py [options]:\n" + header, description="" )
    
    fakegroup = OptionGroup(parser, "Fake DNS records:")

    fakegroup.add_option('--file', action="store", help="Specify a file containing a list of DOMAIN=IP pairs (one pair per line) used for DNS responses. For example: google.com=1.1.1.1 will force all queries to 'google.com' to be resolved to '1.1.1.1'. IPv6 addresses will be automatically detected. You can be even more specific by combining --file with other arguments. However, data obtained from the file will take precedence over others.")
   
    rungroup = OptionGroup(parser,"Optional runtime parameters.")
    rungroup.add_option("--nameservers", metavar="8.8.8.8#53 or 2001:4860:4860::8888", default='8.8.8.8', action="store", help='A comma separated list of alternative DNS servers to use with proxied requests. Nameservers can have either IP or IP#PORT format. A randomly selected server from the list will be used for proxy requests when provided with multiple servers. By default, the tool uses Google\'s public DNS server 8.8.8.8 when running in IPv4 mode and 2001:4860:4860::8888 when running in IPv6 mode.')
    rungroup.add_option("-i","--interface", metavar="127.0.0.1 or ::1", default="127.0.0.1", action="store", help='Define an interface to use for the DNS listener. By default, the tool uses 127.0.0.1 for IPv4 mode and ::1 for IPv6 mode.')
    rungroup.add_option("-t","--tcp", action="store_true", default=False, help="Use TCP DNS proxy instead of the default UDP.")
    rungroup.add_option("-6","--ipv6", action="store_true", default=False, help="Run in IPv6 mode.")
    rungroup.add_option("-p","--port", action="store", metavar="53", default="53", help='Port number to listen for DNS requests.')
    rungroup.add_option("-q", "--quiet", action="store_false", dest="verbose", default=True, help="Don't show headers.")
    parser.add_option_group(rungroup)

    (options,args) = parser.parse_args()
 
    # Print program header
    if options.verbose:
        print header

    interestingdomains = []
    interestingdomainsng = {} #Dict to hold mapping from VPN int to interesting domains
    existingroutes = []
    db_dns_vpn_server = []
    db_dns_upstream_server = []
    
    # Main storage of domain filters
    # NOTE: RDMAP is a dictionary map of qtype strings to handling classses
    nametodns = dict()
    for qtype in RDMAP.keys():
        nametodns[qtype] = dict()
    
    # Notify user about alternative listening port
    if options.port != "53":
        print "[*] Listening on an alternative port %s" % options.port

    print "[*] dsvr started on interface: %s " % options.interface

    # External file definitions
    if options.file:
        config = ConfigParser()
        if "/" not in options.file:
            options.file = os.path.abspath(os.path.dirname(sys.argv[0])) + "/" + options.file
        config.read(options.file)
        print "[*] Using external config file: %s" % options.file
            
        db_dns_upstream_server.append(config.get('Global','dns-upstream-server'))
        print "[*] Using the following nameservers for un-interesting domains: %s" % ", ".join(db_dns_upstream_server)
        nameservers = db_dns_upstream_server
        db_dns_vpn_server.append(config.get('Global','dns-vpn-server'))
        print "[*] Using the following nameservers for interesting domains: %s" % ", ".join(db_dns_vpn_server)
        db_ttl_override_value = config.get('Global','ttl-override-value')
        print "[*] TTL overide value for interesting domains: %s" % db_ttl_override_value
                
        my_dict = getpeerdata()
                
        for indexitem in my_dict:
            peer_options = []
            peer_detail = {}
            for listitem in my_dict[indexitem]:
                key = listitem.split(' ',1)
                if "#interestingdomains" in key:
                    interestingdomainsng[indexitem] = listitem.split(' ',2)[1].split(",")
                    print "[*] Adding interesting domains to %s: %s" % (indexitem,listitem.split(' ',2)[1])
                
    # Clear existing IP Rules #DB
    for index in interestingdomainsng:
        tablenumstr = re.findall(r'\d+',index)
        tablenumint = int(tablenumstr[0]) + 1
        print "[*] Clearing existing IP Rules (Table %s)" % str(tablenumint)
        command = os.path.abspath(os.path.dirname(sys.argv[0])) + "/scripts/iprule-clear-table.sh " + str(tablenumint)
        os.system(command)
    
    # Add selected DNS servers to route via the VPN
    if interestingdomainsng:
        for interfacename in interestingdomainsng:
            intname = interfacename
            break 
 
        for item in db_dns_vpn_server:
            print "[*] Routing DNS server (%s) via first specificed int (%s)" % (item, intname)
            command = "sudo " + os.path.abspath(os.path.dirname(sys.argv[0])) + "/scripts/addroutetorule.sh " + item + " " + intname #DB
            os.system(command)
    
    # Launch dsvr
    start_cooking(interface=options.interface, nametodns=nametodns, nameservers=nameservers, tcp=options.tcp, ipv6=options.ipv6, port=options.port)

