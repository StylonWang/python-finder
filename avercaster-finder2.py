#!/usr/bin/python
# This tool searches for AVerCaster series product in the local LAN,
# by sending SSDP requests and receive replies.
#
# Works for F239, F239+ and F236.

import socket
import struct
import re
import time
import urllib2, urllib
import xml.etree.ElementTree as ET
import select
import get_ip_address
import getopt, sys
import os

MCAST_GRP = '239.255.255.250'
MCAST_PORT = 1900
MSG = "M-SEARCH * HTTP/1.1\r\nST: urn:schemas-avermedia-com:avercaster:1\r\nMX: 10\r\nMAN: \"ssdp:discover\"\r\nHOST: 239.255.255.250:1900\r\n\r\n"
TIME_OUT = 5
INTERFACE = "eth0"

def usage():
    print
    print "[-h]             print this help message"
    print "[-i interface]   select network interface, default", INTERFACE
    print

# parse command-line options
try:  
    opts, args = getopt.getopt(sys.argv[1:], "hi:", [])  
except getopt.GetoptError:  
    print "failed parsing options"
    exit()

for o, a in opts: 
    if o in ("-h"):
        usage()
        exit()
    if o in ("-i"):
        INTERFACE = a

local_ip = get_ip_address.get_ip_address(INTERFACE)
print "Use local interface:", local_ip

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
sock.setblocking(0)
sock.bind( (local_ip, 0) )

mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

avercasters = {}
start_time = time.time()

# send M-SEARCH
sock.sendto(MSG, (MCAST_GRP, MCAST_PORT))

# receive response
while True:

    # implement non-blocking so we can timeout
    curr_time = time.time()
    if curr_time-start_time >= TIME_OUT :
        break
    ready = select.select([sock], [], [], 1);
    if not ready[0] :
        # send M-SEARCH
        print "Searching..."
        sock.sendto(MSG, (MCAST_GRP, MCAST_PORT))
        continue

    # receive messages
    msg = sock.recvfrom(1024)

    reply = re.match("^HTTP/[0-9]\.[0-9] 200.*", msg[0])
    if not reply :
        print "Not HTTP 200 OK"
        print msg[0]
        continue # not a successfull HTTP reply

    if not re.search("ST: urn:schemas-avermedia-com:avercaster:1", msg[0]) :
        print "not AVerCaster"
        #print msg[0]
        continue # not a AVerCaster SSDP NOTIFY message, skip

    device = { 'msg': '', 'ip1': '0.0.0.0', 'ip2': '0.0.0.0',
               'mac1': '', 'mac2': '', 'model': '',
               'version': ''}

    device['msg'] = msg[0]
    device['ip1'] = msg[1][0]

    avercasters[msg[1][0]] = device; # insert by IP address

    #print "[Message]: "
    #print msg[0]

print "Collection done, start querying"

#print avercasters
for key in avercasters :
    #print avercasters[key]['ip1']
    #print avercasters[key]['msg']
    m = re.search("Location: (.*)", avercasters[key]['msg'])
    if not m :
        print "Cannot find location of key: ", key
        continue

    print "checking URL: ", m.group(1)
    
    # don't use proxy. 
    os.environ['http_proxy'] = ''
    os.environ['htts_proxy'] = ''
    # TODO: don't use proxy. set timeout
    try:
        info = urllib2.urlopen(m.group(1), None, 8).read()
        #print info
    except urllib2.URLError:
        print "Unable to connect to ", m.group(1)
        continue

    # parsing XML
    root = ET.fromstring(info)
    
    try:
        avercasters[key]['model'] = root.find('product_name').text
    except AttributeError:
        print "cannot find product_name tag"
    
    try:
        avercasters[key]['mac1'] = root.find('mac').text
    except AttributeError:
        print "cannot find mac tag"

    try:
        avercasters[key]['mac2'] = root.find('mac2').text
    except AttributeError:
        print "cannot find mac2 tag"
    
    try:
        avercasters[key]['version'] = root.find('fw_ver').text
    except AttributeError:
        print "cannot find fw_ver tag"


print
print "Found", len(avercasters), "products"
for key in avercasters :
    print
    print "Model:", avercasters[key]['model']
    print "IP:", avercasters[key]['ip1']
    print "MAC 1:", avercasters[key]['mac1']
    print "MAC 2:", avercasters[key]['mac2']

