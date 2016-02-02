#!/usr/bin/python
import socket
import sys

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('10.1.9.59', 79)
secret = "\x84\x37\x59"

try:
        # Send data
        sent = sock.sendto(secret, server_address)

finally:
        print >>sys.stderr, 'closing socket'
        sock.close()
