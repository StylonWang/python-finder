#
#

import socket
import struct
import re
import time
import urllib2, urllib
import select
import json
import xml.etree.ElementTree as ET
import getopt, sys
import os

def is_f239_plus(version):
        m = re.search("([0-9]*)\.([0-9]*)\.([0-9]*)", version)
        if not m :
            print "cannot parse version", version
            return 0

        version_number = m.group(1)*10000 + m.group(2)*100 + m.group(3)
        # if version is 1.5 and before, it is F239
        # otherwise, it is F239+
        if version_number >= 100600 :
            return 1
        else :
            return 0

def finder2_find_product():

    MCAST_GRP = '239.255.255.250'
    MCAST_PORT = 1900
    MSG = "M-SEARCH * HTTP/1.1\r\nST: urn:schemas-avermedia-com:avercaster:1\r\nMX: 10\r\nMAN: \"ssdp:discover\"\r\nHOST: 239.255.255.250:1900\r\n\r\n"
    TIME_OUT = 2

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    sock.setblocking(0)
#    sock.bind( (local_ip, 0) )

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
#            print "Not HTTP 200 OK"
#            print msg[0]
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

#        print "[Message]: "
        print msg[1][0]
        print msg[0]

    print "Collection done, start querying"

    #print avercasters
    for key in avercasters :
        print avercasters[key]['ip1']
        print avercasters[key]['msg']
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
            #avercasters[key]['model'] = root.find('product_name').text
            avercasters[key]['model'] = root.find('update_name').text
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

        if avercasters[key]['model'] == 'F239' and is_f239_plus(avercasters[key]['version']) :
            avercasters[key]['model'] = 'F239+'

#    print
#    print "Found", len(avercasters), "products"
#    for key in avercasters :
#        print
#        print "Model:", avercasters[key]['model']
#        print "IP:", avercasters[key]['ip1']
#        print "MAC 1:", avercasters[key]['mac1']
#        print "MAC 2:", avercasters[key]['mac2']

    return avercasters

def id_to_mac(id):
        id = id.upper()
        return id[0] + id[1] + ":" + id[2] + id[3] + ":" + \
               id[4] + id[5] + ":" + id[6] + id[7] + ":" + \
               id[8] + id[9] + ":" + id[10] + id[11]

def finder3_find_product():
    
    MCAST_GRP = '234.8.8.8'
    MCAST_PORT = 8888
    MSG = "{\n\"Command\":\"browse\"\n}"
    TIME_OUT = 2

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
        #print "Searching..."
        #print msg[0]

        # parsing JSON 
        try:
            data = json.loads(msg[0])
            command = data["command"]
        except (ValueError, KeyError, TypeError):
            #print "JSON format error: command"
            continue

        if not command == "browse_response" :
            #print "skip non-browse-response", command
            continue
            
        device = { 'msg': '', 'ip1': '0.0.0.0', 'ip2': '0.0.0.0',
                   'mac1': '', 'mac2': '', 'model': '',
                   'version': '', 'name': ''}

        try:
            device['msg'] = msg[0]
            device['ip1'] = msg[1][0]
            device['model'] = data['model']
            device['version'] = data['master_version']
            device['mac1'] = id_to_mac(data['nic'][0]['id'])
            device['name'] = data['device_name']
        except (ValueError, KeyError, TypeError):
            #print "JSON format error: other"
            continue

        #print "Add ", device['ip1']
        avercasters[msg[1][0]] = device; # insert by IP address

    return avercasters
    #print
    #print "Found", len(avercasters), "products"
    #for key in avercasters :
    #    print
        #print avercasters[key]['msg']
    #    print "Name:", avercasters[key]['name']
    #    print "Model:", avercasters[key]['model']
    #    print "IP:", avercasters[key]['ip1']
    #    print "MAC:", avercasters[key]['mac1']

