#!/usr/bin/python
#
# This tool searches for AVerCaster series product in the local LAN,
# by listening to SSDP NOTIFY messages. This only works on F239/F239+, not F236.
#
# Known issues: if not enough SSDP NOTIFY messages are received,
#               first while loop will not end because sock.recvfrom is blocking.
#

import socket
import struct
import re
import time
import urllib2, urllib
import xml.etree.ElementTree as ET

MCAST_GRP = '239.255.255.250'
MCAST_PORT = 1900

WORK_TIME = 5 # default to collect SSDP for 10 seconds

# set up to receive SSDP multicast messages
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((MCAST_GRP, MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
 
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

avercasters = {}
start_time = time.time()
 
# receive SSDP messages
while True:
    #print sock.recv(1024)
    msg = sock.recvfrom(1024)
    if not re.match("^NOTIFY", msg[0]) :
        continue # not a SSDP NOTIFY message, skip

    if not re.search("NT: urn:schemas-avermedia-com:avercaster:1", msg[0]) :
        print "not AVerCaster"
        #print msg[0]
        continue # not a AVerCaster SSDP NOTIFY message, skip

    #print msg[0]
    print "NOTIFY from", msg[1][0]
    #print msg[1][0] #ip address
    
    device = { 'msg': '', 'ip1': '0.0.0.0', 'ip2': '0.0.0.0',
               'mac1': '', 'mac2': '', 'model': '',
               'version': ''}

    device['msg'] = msg[0]
    device['ip1'] = msg[1][0]

    avercasters[msg[1][0]] = device; # insert by IP address

    curr_time = time.time()
    if curr_time-start_time > WORK_TIME :
        break

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
    
    try:
        info = urllib2.urlopen(m.group(1)).read()
        #print info
    except urllib2.URLError:
        print "Unable to connect to ", m.group(1)
        continue

    # parsing XML
    root = ET.fromstring(info)
    
    product_tag = root.find('product_name')
    avercasters[key]['model'] = product_tag.text
    avercasters[key]['mac1'] = root.find('mac').text
    avercasters[key]['mac2'] = root.find('mac2').text
    avercasters[key]['version'] = root.find('fw_ver').text


print "Found", len(avercasters), "products"
for key in avercasters :
    print "Model:", avercasters[key]['model']
    print "IP:", avercasters[key]['ip1']
    print "MAC 1:", avercasters[key]['mac1']
    print "MAC 2:", avercasters[key]['mac2']

