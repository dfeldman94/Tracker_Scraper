"""
Author: shadyabhi abhijeet.1989@gmail.com
For protocol description(not mine), check http://bittorrent.org/beps/bep_0015.html#udp-tracker-protocol
"""

import socket
import struct   
from random import randrange #to generate random transaction_id
from urllib2 import urlopen
from contextlib import closing
import json
import re
import requests
import time

tracker = "open.demonii.com"

port = 1337
torrent_hash = "37b3f09596c26eec5c2aebfc6c36e3fafec46450"
torrent_details = {}
torrent_IP = {}

def get_torrent_name(infohash):
    url = "http://torrentz.me/" + infohash
    p = urlopen(url)
    page = p.read()
    c = re.compile(r'<h2><span>(.*?)</span>')
    return c.search(page).group(1)

def pretty_show(infohash):
    print "Torrent Hash: ", infohash
    try:
        print "Torrent Name (from torrentz): ", get_torrent_name(infohash)
    except:
        print "Coundn'f find torrent name"
    print "Seeds, Leechers, Completed", torrent_details[infohash] 
    print 

def print_torrent_IP(infohash):
    for IP in torrent_IP[infohash]:
        print IP

def get_geolocation_for_ip(ip):
    GEO_IP_url = 'http://freegeoip.net/json/'
    url = '{}/{}'.format(GEO_IP_url, ip)

    response = requests.get(url)
    response.raise_for_status()

    return response.json()

def connect_to_tracker(clisocket):
    #Protocol says to keep it this way (FOR UDP???)
    connection_id=0x41727101980
    #We should get the same in response
    send_trans_id = randrange(1,65535)

    #CLient connects to torrent tracker. Middle Number is "request" id; 0 is request for connection
    packet=struct.pack(">QLL",connection_id, 0, send_trans_id)
    clisocket.send(packet)
    res = clisocket.recv(16)
    action,rec_trans_id,connection_id=struct.unpack(">LLQ",res)
    if not (send_trans_id == rec_trans_id):
        print("Error: transaction ID mismatch")
        #How to exit??
    return connection_id



def scrape_tracker(infohash, connection_ID, clisocket):
    packet_hash = infohash.decode('hex')

    transaction_id = randrange(1,65535)
    #Construct packet to scrape tracker
    packet = struct.pack(">QLL", connection_ID, 2, transaction_id) + packet_hash
    clisocket.send(packet)
    res = clisocket.recv(8 + 12)

    index = 8
    seeders, completed, leechers = struct.unpack(">LLL", res[index:index+12])
    torrent_details[infohash] = (seeders, leechers, completed)
    pretty_show(infohash)



def get_tracker_IPs(infohash, connection_ID, clisocket, num_want=50, port=8080):
    packet_hash = infohash.decode('hex')
    #Get new transaction ID
    transaction_id = randrange(1,65535)
    peer_id = '%030x' % randrange(16**20)
    #num_want = 200
    #Construct packet to announce to tracker
    announce_packet = struct.pack(">QLL", connection_ID, 1, transaction_id) + packet_hash + peer_id + struct.pack(">QQQLLLlH", 0, 0, 0, 2, 0, 0, num_want, port)
    clisocket.send(announce_packet)
    res = clisocket.recv(20 + (6 * num_want))


    #Check to see if we received an error
    if(struct.unpack(">L", res[0:4]) == 3):
        print("Tracker returned error: " + res[8:len(res)])
        exit(1)

    index = 8
    interval, leechers, seeders = struct.unpack(">LLL", res[index:index + 12])
    index = 20
    peer_IPs = []
    for i in range(0,num_want):
        ip = socket.inet_ntoa(res[index:index + 4])
        print("Getting location for " + ip + "...")
        ip_location = get_geolocation_for_ip(ip)
        print(ip_location)
        #u_port = struct.unpack(">H", res[index + 4: index + 6])
        #(torrent_IP[infohash]).append()
        peer_IPs.append({"IP":ip, "city":ip_location['city'], "country":ip_location['country_name']})#{"IP": ip, "Port": u_port, "city":ip_location['city'], "country":ip_location['country_name']})#struct.unpack(">L", res[index:index + 4])
        index += 6
    for IP in peer_IPs:
        print(IP)

def add_unique_IPs(infohash, connection_ID, clisocket, num_want=50, attempts=1, delay=.5, port=8080):
    packet_hash = infohash.decode('hex')

    peer_id = '%030x' % randrange(16**20)
    #num_want = 200

    for j in range(0,attempts):
        #Get new transaction ID
        last_len = 0 if torrent_IP[infohash] is None else len(torrent_IP[infohash])
        transaction_id = randrange(1,65535)
        #Construct packet to announce to tracker
        announce_packet = struct.pack(">QLL", connection_ID, 1, transaction_id) + packet_hash + peer_id + struct.pack(">QQQLLLlH", 0, 0, 0, 2, 0, 0, num_want, port)
        clisocket.send(announce_packet)
        res = clisocket.recv(20 + (6 * num_want))


        #Check to see if we received an error
        if(struct.unpack(">L", res[0:4]) == 3):
            print("Tracker returned error: " + res[8:len(res)])
            exit(1)

        index = 8
        interval, leechers, seeders = struct.unpack(">LLL", res[index:index + 12])
        index = 20
        peer_IPs = []
        for i in range(0,num_want):
            ip = socket.inet_ntoa(res[index:index + 4])
            #ip_location = get_geolocation_for_ip(ip)
            #u_port = struct.unpack(">H", res[index + 4: index + 6])
            if ip not in torrent_IP[infohash]:
                ip_location = get_geolocation_for_ip(ip)
                (torrent_IP[infohash]).append({"IP":ip, "city":ip_location['city'], "country":ip_location['country_name']})
                #torrent_IP[infohash].append(ip)
            #peer_IPs.append(ip)#{"IP": ip, "Port": u_port, "city":ip_location['city'], "country":ip_location['country_name']})#struct.unpack(">L", res[index:index + 4])
            index += 6

        print("New IPs added: " + str(len(torrent_IP[infohash]) - last_len))
        print("Total IPs: " + str(len(torrent_IP[infohash])))
        time.sleep(delay)




#Create the socket
clisocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clisocket.connect((tracker, port))

connection_ID = connect_to_tracker(clisocket)
torrent_IP[torrent_hash] = []
#print(get_geolocation_for_ip("90.154.73.111"))
scrape_tracker(torrent_hash, connection_ID, clisocket)

#get_tracker_IPs(torrent_hash, connection_ID, clisocket, 10)

add_unique_IPs(torrent_hash, connection_ID, clisocket, 20, 3, 1)

print_torrent_IP(torrent_hash)


"""
#Protocol says to keep it this way (FOR UDP???)
connection_id=0x41727101980
#We should get the same in response
transaction_id = randrange(1,65535)

#CLient connects to torrent tracker. Middle Number is "request" id; 0 is request for connection
packet=struct.pack(">QLL",connection_id, 0,transaction_id)
clisocket.send(packet)
res = clisocket.recv(16)
action,transaction_id,connection_id=struct.unpack(">LLQ",res)

packet_hashes = ""
packet_hash = torrent_hash[0].decode('hex')
for infohash in torrent_hash:
    packet_hashes = packet_hashes + infohash.decode('hex')

#Construct packet to scrape tracker
packet = struct.pack(">QLL", connection_id, 2, transaction_id) + packet_hashes

#Get new transaction ID
transaction_id = randrange(1,65535)
#Generate our peer_id, a 20 bit number
peer_id = '%030x' % randrange(16**20)
#Choose port?
port2 = 8080
num_want = 200
#Construct packet to announce to tracker
announce_packet = struct.pack(">QLL", connection_id, 1, transaction_id) + packet_hash + peer_id + struct.pack(">QQQLLLlH", 0, 0, 0, 2, 0, 0, num_want, port2)

#print(len(packet_hashes))
#print(struct.unpack(">QLL", packet[0:-len(packet_hashes)]))

clisocket.send(packet)
res = clisocket.recv(8 + 12*len(torrent_hash))

index = 8
for infohash in torrent_hash:
    seeders, completed, leechers = struct.unpack(">LLL", res[index:index+12])
    torrent_details[infohash] = (seeders, leechers, completed)
    pretty_show(infohash)
    index = index + 12

clisocket.send(announce_packet)
res = clisocket.recv(20 + (6 * num_want))

print(len(res))

#Check to see if we received an error
if(struct.unpack(">L", res[0:4]) == 3):
    print("Tracker returned error: " + res[8:len(res)])
    exit(1)

index = 8
interval, leechers, seeders = struct.unpack(">LLL", res[index:index + 12])
index = 20
peer_IPs = []
for i in range(0,num_want):
    ip = socket.inet_ntoa(res[index:index + 4])
    #ip_location = get_geolocation_for_ip(ip)
    #u_port = struct.unpack(">H", res[index + 4: index + 6])
    peer_IPs.append(ip)#{"IP": ip, "Port": u_port, "city":ip_location['city'], "country":ip_location['country_name']})#struct.unpack(">L", res[index:index + 4])
    index += 6
for IP in peer_IPs:
    print(IP)

"""






