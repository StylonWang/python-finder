#!/usr/bin/python

import socket
import struct
import getopt, sys

MCAST_GRP = '239.255.255.250'
MCAST_PORT = 1900

def usage():
    print
    print "[-h]             print this help message"
    print "[-g multicast-group-ip]   multicast IP to listen to. Default", MCAST_GRP
    print "[-p multicast-port] multicast port to listen to. Detault", MCAST_PORT
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

print "Will listen to multicast", MCAST_GRP, MCAST_PORT 

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((MCAST_GRP, MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
 
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
 
count = 0
while True:
    #print sock.recv(1024)
    msg = sock.recvfrom(1024)
    print "[Message]", count
    print msg[0]
    print "[Address]", count
    print msg[1][0]
    print "----------------- delimiter --------------------\n"
    count += 1

