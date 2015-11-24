#!/usr/bin/python

import socket
import struct
import re
import time
import urllib2, urllib
import select
import json
import getopt, sys

MCAST_GRP = '239.255.255.0'
MCAST_PORT = 1900
MSG = "{\n\"Command\":\"browse\"\n}"
TIME_OUT = 3

def usage():
    print
    print "[-h]             print this help message"
    print "[-g multicast-group-ip]   multicast IP to send to. Default", MCAST_GRP
    print "[-p multicast-port] multicast port to send to. Detault", MCAST_PORT
    print

# parse command-line options
try:  
    opts, args = getopt.getopt(sys.argv[1:], "hg:p:", [])  
except getopt.GetoptError:  
    print "failed parsing options"
    exit()

for o, a in opts: 
    if o in ("-h"):
        usage()
        exit()
    if o in ("-g"):
        MCAST_GRP = a
    if o in ("-p"):
        MCAST_PORT = a

print "Will send to multicast", MCAST_GRP, MCAST_PORT 

# set up sender socket
ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
ssock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#ssock.bind( ("0.0.0.0", MCAST_PORT) )

start_time = time.time()

# send browse command
ssock.sendto(MSG, (MCAST_GRP, MCAST_PORT))

