import socket
import struct  
from random import randrange #to generate random transaction_id
from urllib2 import urlopen
from contextlib import closing
import json
import re
import requests
import time
#Class for representing tracker for a torrent
class Tracker(object):
	def __init__(self, info_hash, serv_type, URL, port):
		self.info_hash = info_hash
		self.serv_type = serv_type
		self.URL = URL
		self.port = port
		self.IP = []
		#self.connection_id=0x41727101980

	#Connect to UDP tracker, return tuple with new socket, connection ID. 
	def connect(self):
		#Create the socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		print(self.sock)
		self.sock.connect((self.URL, self.port))
		#self.sock = sock

		#Init connection packet vars
		#Protocol dictates to use self connection ID to initialize
		self.connection_id=0x41727101980
		#Choose random transaction ID
		send_trans_id = randrange(1,65535)
		self.peer_id = '%030x' % randrange(16**20)

		#CLient connects to torrent tracker. Middle Number is "request" id; 0 is request for connection
		packet=struct.pack(">QLL",self.connection_id, 0, send_trans_id)
		self.sock.send(packet)

		#Receive response; comes in form (action, transaction id, connection id)
		res = self.sock.recv(16)
		action,rec_trans_id,self.connection_id = struct.unpack(">LLQ",res)
		#Check if we received same transaction id as we sent
		if not (send_trans_id == rec_trans_id):
			print("Error: transaction ID mismatch")
			#How to exit??
		return self.sock, self.connection_id

	def disconnect(self):
		self.sock.close()

	#Send scrape request to torrent. Return tuple: (seeders, leechers, completed)
	def scrape(self):
		packet_hash = self.info_hash.decode('hex')
		transaction_id = randrange(1,65535)

		#Construct packet to scrape tracker
		packet = struct.pack(">QLL", self.connection_id, 2, transaction_id) + packet_hash
		self.sock.send(packet)
		res = self.sock.recv(8 + 12)
		index = 8
		self.seeders, self.completed, self.leechers = struct.unpack(">LLL", res[index:index+12])
		#torrent_details[infohash] = (seeders, leechers, completed)
		return (self.seeders, self.leechers, self.completed)

	#Get the requested num of ips from the tracker. 
	def req_IPs(self, num_want=50, port=8080, attempts=1, delay=.5):
		packet_hash = self.info_hash.decode('hex')

		for j in range(0, attempts):
			#Get new transaction ID
			transaction_id = randrange(1,65535)

			#Construct packet to announce to tracker
			announce_packet = struct.pack(">QLL", self.connection_id, 1, transaction_id) + packet_hash + self.peer_id + struct.pack(">qqqlLLlH", 0, 0, 0, 2, 0, 0, num_want, port)
			self.sock.send(announce_packet)
			res, addr = self.sock.recvfrom(1220)
			recvd_IPs = (len(res) - 20)/6
			print(recvd_IPs)

			#Check to see if we received an error
			if(struct.unpack(">L", res[0:4]) == 3):
				print("Tracker returned error: " + res[8:len(res)])
				exit(1)

			index = 8
			self.interval, self.leechers, self.seeders = struct.unpack(">LLL", res[index:index + 12])
			index = 20
			peer_IPs = []
			for i in range(0,recvd_IPs):
				ip = socket.inet_ntoa(res[index:index + 4])
			#print("Getting location for " + ip + "...")
			#ip_location = get_geolocation_for_ip(ip)
			#print(ip_location)
			#u_port = struct.unpack(">H", res[index + 4: index + 6])
			#(torrent_IP[infohash]).append()
			#peer_IPs.append({"IP":ip, "city":ip_location['city'], "country":ip_location['country_name']})#{"IP": ip, "Port": u_port, "city":ip_location['city'], "country":ip_location['country_name']})#struct.unpack(">L", res[index:index + 4])
				if ip not in self.IP:
					self.IP.append(ip)
					peer_IPs.append(ip)
				index += 6
			time.sleep(delay)
		return peer_IPs

	def print_details(self, IP=False):
		print("Seeders: ", self.seeders)
		print("Leechers: ", self.leechers)
		print("Completed: ", self.completed)
		if IP:
			self.print_IP()
	def print_IP(self):
		for IP in self.IP:
			print(IP)

