#!/usr/bin/python
#
# Simulate a fake SE510 clients to receive and respond to search queries 
# from multicast.
#

import socket
import struct
import re
import time
import urllib2, urllib
import select
import json
import json
import random

random.seed()

# generate random response
name = "SE510_" + "fake" + str(random.randint(100, 999))
version = str(random.randint(0, 999)) + "." \
          + str(random.randint(0, 999)) + "." \
        + str(random.randint(0, 999)) + "." 
ip = "10.1." + str(random.randint(1, 253)) + "." \
           + str(random.randint(1, 253)) 
mac = "00181a" + str(random.randint(10, 99)) \
               + str(random.randint(10, 99)) \
               + str(random.randint(10, 99)) 

response = { "command": "browse_response",
	"device_name": name, #"SE510_demo",
	"org": "AVerMedia",
	"model": "SE510",
	"master_version": version,
	"daily": "2015.10.08_09:42:48",
	"uboot_version": "0.0.0",
	"sku": {
		"sub_model": ""
	    },
	"nic": [
		{
			"enable": 1,
			"id": mac,
			"dhcp": "static_ip",
			"name": "eth2",
			"ip": ip,
			"mask": "255.255.0.0",
			"gateway": "10.1.2.254",
			"dns": "10.1.1.57,10.1.1.55",
			"isConnected": 1
		}
	   ],
    }

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
#rsock.setblocking(0)
rsock.bind( (MCAST_GRP, MCAST_PORT) )

mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
rsock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

avercasters = {}
start_time = time.time()

# send browse command
#ssock.sendto(MSG, (MCAST_GRP, MCAST_PORT))
#ssock.send(MSG)

# receive browse command
while True:

    # receive messages
    msg = rsock.recvfrom(1024)
    print "received msg: ", msg[0]

    # parsing JSON 
    try:
        data = json.loads(msg[0])
        command = data["Command"]
    except (ValueError, KeyError, TypeError):
        #print "JSON format error"
        continue

    if not command == "browse" :
        print "skip non-browse message"
        continue

    time.sleep( random.uniform(0.1, 0.9) )
    response_j = json.dumps(response)
    ssock.sendto(response_j, (MCAST_GRP, MCAST_PORT))
    print response_j
        
