#!/usr/bin/python
# This tool searches for AVerCaster series product in the local LAN,
# by sending specialized multicast messages.
#
# Works for SE510.

import socket
import struct
import re
import time
import urllib2, urllib
import select
import json

MCAST_GRP = '234.8.8.8'
MCAST_PORT = 8888
MSG = "{\n\"Command\":\"browse\"\n}"
TIME_OUT = 3

# set up sender socket
ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
ssock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#ssock.bind( ("0.0.0.0", MCAST_PORT) )

# set up receiver socket
rsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
rsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#rsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
rsock.setblocking(0)
rsock.bind( (MCAST_GRP, MCAST_PORT) )

mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
rsock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

avercasters = {}
start_time = time.time()

# send browse command
ssock.sendto(MSG, (MCAST_GRP, MCAST_PORT))
#ssock.send(MSG)

# receive response
while True:

    # implement non-blocking so we can timeout
    curr_time = time.time()
    if curr_time-start_time >= TIME_OUT :
        break
    ready = select.select([rsock], [], [], 1);
    if not ready[0] :
        # send browse command
        ssock.sendto(MSG, (MCAST_GRP, MCAST_PORT))
        continue

    # receive messages
    msg = rsock.recvfrom(1024)

    #print "[Message]: " , msg[1][0]
    print "Searching..."
    #print msg[0]

    # parsing JSON 
    try:
        data = json.loads(msg[0])
        command = data["command"]
    except (ValueError, KeyError, TypeError):
        #print "JSON format error"
        continue

    if not command == "browse_response" :
        print "skip non-browse-response"
        continue
        
    device = { 'msg': '', 'ip1': '0.0.0.0', 'ip2': '0.0.0.0',
               'mac1': '', 'mac2': '', 'model': '',
               'version': '', 'name': ''}

    try:
        device['msg'] = msg[0]
        device['ip1'] = msg[1][0]
        device['model'] = data['model']
        device['version'] = data['master_version']
        device['mac1'] = data['nic'][0]['id']
        device['name'] = data['device_name']
    except (ValueError, KeyError, TypeError):
        print "JSON format error"
        continue

    #print "Add ", device['ip1']
    avercasters[msg[1][0]] = device; # insert by IP address

print
print "Found", len(avercasters), "products"
for key in avercasters :
    print
    #print avercasters[key]['msg']
    print "Name:", avercasters[key]['name']
    print "Model:", avercasters[key]['model']
    print "IP:", avercasters[key]['ip1']
    print "MAC:", avercasters[key]['mac1']

