"""
Author: Dylan Feldman

Tracker object definition for use in tracker scraper program
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
import sys
import util
import binascii
import urllib
import bencode
from urlparse import urlparse, urlunsplit



#Class for representing tracker for a torrent
class Tracker(object):
	def __init__(self, info_hash, serv_type, URL, port):
		self.info_hash = info_hash
		self.serv_type = serv_type
		self.URL = URL
		self.port = port
		self.peer_id = '%030x' % randrange(16**20)
		self.IP = []
		self.geo_info = {}
		print(serv_type)
		self.connected = False if (serv_type.lower() == "udp") else True
		#self.connection_id=0x41727101980

	#Connect to UDP tracker, return tuple with new socket, connection ID. 
	def _connect_UDP(self):
		#Create the socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.connect((self.URL, self.port))
		#self.sock = sock

		#Init connection packet vars
		#Protocol dictates to use self connection ID to initialize
		self.connection_id=0x41727101980
		#Choose random transaction ID
		send_trans_id = randrange(1,65535)
		

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
		self.connected = True
		return self.sock, self.connection_id

	def disconnect(self):
		self.sock.close()

	#Send scrape request to torrent. Return tuple: (seeders, leechers, completed)
	def scrape(self):
		if self.serv_type in ["http", "https"]:
			return self._scrape_http()
		else:
			if not self.connected:
				self._connect_UDP()
			return self._scrape_UDP()


	#Send scrape request to torrent. Return tuple: (seeders, leechers, completed)
	def _scrape_UDP(self):
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
			recvd_IPs = self._announce_UDP(num_want) if (self.serv_type.lower() == "udp") else self._announce_http(num_want)
			peer_IPs = 0
			for ip in recvd_IPs:
				#ip = socket.inet_ntoa(res[index:index + 4])
			#u_port = struct.unpack(">H", res[index + 4: index + 6])

				#{"IP": ip, "Port": u_port, "city":ip_location['city'], "country":ip_location['country_name']})#struct.unpack(">L", res[index:index + 4])
				if ip not in self.IP:
					self.IP.append(ip)
					peer_IPs += 1
					ip_location = util.get_geolocation_for_ip(ip)
					ip_location = (ip_location['country_name'], ip_location['city']) if ip_location['city'] else (ip_location['country_name'])
					print(ip_location)
					if ip_location not in self.geo_info.keys():
						#print("HHH")
						self.geo_info[ip_location] = 1
					else:
						self.geo_info[ip_location] += 1
			time.sleep(delay)
		return peer_IPs

	def _announce_UDP(self, num_want):
		#Get new transaction ID
		transaction_id = randrange(1,65535)

		#Construct packet to announce to tracker
		announce_packet = struct.pack(">QLL", self.connection_id, 1, transaction_id) + self.info_hash.decode('hex') + self.peer_id + struct.pack(">qqqlLLLH", 0, 0, 0, 2, 0, 0, 511, self.port)
		self.sock.send(announce_packet)
		res, addr = self.sock.recvfrom(1220)#(20 + (6 * num_want)) #1220
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
		for i in range(0, recvd_IPs):
			ip = socket.inet_ntoa(res[index:index + 4])
			#u_port = struct.unpack(">H", res[index + 4: index + 6])
			peer_IPs.append(ip)
			index += 6
		return peer_IPs


	def _scrape_http(self):
		tracker = self.serv_type + "://" + self.URL + ":" + str(self.port) + "/scrape"
		hashed = binascii.a2b_hex(self.info_hash)
		hashed = urllib.quote_plus(hashed)
		encoding = urllib.urlencode({ 'infohash' : self.info_hash})
		url = tracker + "?info_hash=" + hashed
		txt = urlopen(url, timeout=1).read()
		data = bencode.bdecode(txt)
		print(data)
		torrent_details = (data["complete"], data["incomplete"])
		return torrent_details

	def _announce_http(self, num_want):
		tracker = self.serv_type + "://" + self.URL + ":" + str(self.port) + "/announce"
		hashed = binascii.a2b_hex(self.info_hash)
		hashed = urllib.quote_plus(hashed)
		url = tracker + "?info_hash=" + hashed + "&peer_id=12345678987654321234&port=" + str(self.port) + "&uploaded=0&downloaded=0&left=0&compact=1&event=started&numwant=" + str(num_want)
		print(url)
		txt = urlopen(url, timeout=200).read()
		data = bencode.bdecode(txt)
		print(data)
		peers = data['peers']
		peer_IPs = []
		index = 0
		for i in range(0,num_want - 1):
			
			ip = socket.inet_ntoa(peers[index:(index + 4)])
			#u_port = struct.unpack(">H", res[index + 4: index + 6])
			peer_IPs.append(ip)
			index += 6
		return peer_IPs

	def print_details(self, geo=False, IP=False):
		print("Seeders: ", self.seeders)
		print("Leechers: ", self.leechers)
		print("Completed: ", self.completed)
		if geo:
			#print(self.geo_info)
			for loc in self.geo_info.keys():
				formatted_line = ""
				if type(loc) is tuple:
					formatted_line = loc[0] + ", " + loc[1]
				else:
					formatted_line = loc
				formatted_line += ": " + str(self.geo_info[loc])
				print(formatted_line)
		elif IP:
			self.print_IP()

	def print_IP(self):
		for IP in self.IP:
			print(IP)

