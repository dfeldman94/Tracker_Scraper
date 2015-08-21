"""
Author: Dylan Feldman

Tracker object definition for use in tracker scraper program
"""

import socket
import struct
from socket import timeout  
from random import randrange #to generate random transaction_id
from urllib2 import urlopen, URLError
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
import errors

socket.setdefaulttimeout(10)


#Class for representing tracker for a torrent
class Tracker(object):
	def __init__(self, info_hash, serv_type, URL, port, listen_port, name):
		self.name = name
		self.info_hash = info_hash
		self.serv_type = serv_type.lower()
		self.URL = URL
		self.port = port
		self.peer_id = '%030x' % randrange(16**20)
		self.IP = []
		self.geo_info = {}
		self.connected = False#False if (serv_type.lower() == "udp") else True
		self.listen_port = listen_port


	#Send scrape request to torrent. Return tuple: (seeders, leechers, completed)
	def scrape(self):
		if self.serv_type in ["http", "https"]:
			scrape_result = self._scrape_http()
			if not scrape_result:
				return None
			self.seeders, self.leechers, self.completed = scrape_result
			return (self.seeders, self.completed, self.leechers)
		else:
			if not self.connected:
				if(self._connect_UDP()):
					scrape_result = self._scrape_UDP()
					if(not scrape_result):
						return None
					self.seeders, self.completed, self.leechers = scrape_result
				else:
					return None
			return (self.seeders, self.completed, self.leechers)

		

	#Get the requested num of ips from the tracker. 
	def get_IPs(self, num_want=50, port=8080):
		if self.serv_type == "udp" and not self.connected:
			if(not self._connect_UDP()):
				return -1
		packet_hash = self.info_hash.decode('hex')
		recvd_IPs = self._announce_UDP(num_want) if (self.serv_type.lower() == "udp") else self._announce_http(num_want)
		if not recvd_IPs:
			return -1
		unique_IPs = []
		for ip in recvd_IPs:
			if ip not in self.IP:
				self.IP.append(ip)
				unique_IPs.append(ip)
				ip_location = util.get_geolocation_for_ip(ip)
				if not ip_location:
					continue
				loc_key = (ip_location['country'], ip_location['city'])
				if loc_key not in self.geo_info.keys():
					ip_location['n'] = 1
					self.geo_info[loc_key] = ip_location
				else:
					self.geo_info[loc_key]['n'] += 1
		return unique_IPs

	def get_all_IPs(self, max_attempts=20, ignore_wait=False, port=8080):
		if not self.connected:
			if(not self.scrape()):
				return None
		try:
			total_IPs = self.leechers + self.seeders
		except AttributeError:
			self.scrape()
			try:
				total_IPs = self.leechers + self.seeders
			except AttributeError:
				return None
		collected_IPs = []
		self.interval = 0
		while(abs(total_IPs - len(collected_IPs)) > 3 and (max_attempts > 0)):
			if not ignore_wait:
				time.sleep(self.interval)
			new_IPs = self.get_IPs(port=port)
			if new_IPs == -1:
				return None
			wait_str = ("Ignoring required wait interval...") if ignore_wait else ("Will wait " + str(self.interval) + " seconds to try again if there are more IPs")
			print("Collected " + str(len(new_IPs)) + " new IPs. " + wait_str) 
			collected_IPs.extend(new_IPs)
			max_attempts -= 1
		return collected_IPs


	def dump_to_file(self, filename, geo=True):
		print("Dumping info to '" + filename + "'...")
		info_file = None
		try:
			info_file = open(filename, "a")
		except OSError:
			print("Error opening file '" + filename + "'\nMake sure the file name is valid, and that you have proper write permissions.")
		try:
			info_file.write("Seeders: " + str(self.seeders) + "\n")
			info_file.write("Leechers: " + str(self.leechers) + "\n")
			info_file.write("Completed: " + str(self.completed) + "\n\n\n")
		except AttributeError:
			print("Error: Tracker " + self.URL + " not successfully scraped before dumping to file")
			info_file.close()
			return None
		if geo:
			#print(self.geo_info)
			for loc in self.geo_info.keys():
				formatted_line = ""
				#if type(loc) is tuple:

				formatted_line = u'' + self.geo_info[loc]['country'] + ", " + self.geo_info[loc]['city']

				#else:
				#	formatted_line = loc
				formatted_line += ": " + str(self.geo_info[loc]['n']) + "\n"
				info_file.write(formatted_line.encode('utf8'))
		info_file.write("\n")
		info_file.close()

	def print_details(self, geo=False, IP=False):
		try:
			print("Seeders: ", self.seeders)
			print("Leechers: ", self.leechers)
			print("Completed: ", self.completed)
		except AttributeError:
			print("Error: Tracker not scraped before printing details")
			return None
		if geo:
			#print(self.geo_info)
			for loc in self.geo_info.keys():
				formatted_line = ""
				#if type(loc) is tuple:

				formatted_line = u'' + self.geo_info[loc]['country'] + ", " + self.geo_info[loc]['city']

				#else:
				#	formatted_line = loc
				formatted_line += ": " + str(self.geo_info[loc]['n']) + "\n"
				print(formatted_line)
		elif IP:
			self.print_IP()

	def print_IP(self):
		for IP in self.IP:
			print(IP)

	#Connect to UDP tracker, return tuple with new socket, connection ID. 
	def _connect_UDP(self):
		#Create the socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			self.sock.connect((self.URL, self.port))
		except socket.gaierror, timeout:
			return None

		#Init connection packet vars
		#Protocol dictates to use self connection ID to initialize
		self.connection_id=0x41727101980
		#Choose random transaction ID
		send_trans_id = randrange(1,65535)
		

		#CLient connects to torrent tracker. Middle Number is "request" id; 0 is request for connection
		packet=struct.pack(">QLL",self.connection_id, 0, send_trans_id)
		self.sock.send(packet)

		#Receive response; comes in form (action, transaction id, connection id)
		res = None
		try:
			res = self.sock.recv(16)
		except socket.timeout:
			return None
		action,rec_trans_id,self.connection_id = struct.unpack(">LLQ",res)
		#Check if we received same transaction id as we sent
		if not (send_trans_id == rec_trans_id):
			print("Error: transaction ID mismatch")
			return None
		self.connected = True
		return self.sock, self.connection_id

	def _disconnect_UDP(self):
		self.sock.close()

	#Send scrape request to torrent. Return tuple: (seeders, leechers, completed)
	def _scrape_UDP(self, retry_attempt=False):
		packet_hash = self.info_hash.decode('hex')
		transaction_id = randrange(1,65535)

		#Construct packet to scrape tracker
		packet = struct.pack(">QLL", self.connection_id, 2, transaction_id) + packet_hash
		self.sock.send(packet)
		try:
			res = self.sock.recv(8 + 12)
		except socket.timeout:
			if(retry_attempt):
				raise TimeoutError
				#return None
			else:
				print("Error: Timed out waiting for " + self.URL + ". Trying again...")
				return self._scrape_UDP(True)
		index = 8
		return struct.unpack(">LLL", res[index:index+12])
		#torrent_details[infohash] = (seeders, leechers, completed)

	def _announce_UDP(self, num_want, retry_attempt=False):

		#Get new transaction ID
		transaction_id = randrange(1,65535)

		#Construct packet to announce to tracker
		announce_packet = struct.pack(">QLL", self.connection_id, 1, transaction_id) + self.info_hash.decode('hex') + self.peer_id + struct.pack(">qqqlLLLH", 0, 0, 0, 2, 0, 0, 511, self.port)
		self.sock.send(announce_packet)
		try:
			res, addr = self.sock.recvfrom(1220)#(20 + (6 * num_want)) #1220
		except socket.timeout:
			if(retry_attempt):
				return None
			else:
				print("Error: Timed out waiting for " + self.URL + ". Trying again...")
				return self._announce_UDP(num_want, True)
		recvd_IPs = (len(res) - 20)/6

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

	def _scrape_http(self, retry_attempt=False):
		tracker = self.serv_type + "://" + self.URL + "/scrape"
		hashed = binascii.a2b_hex(self.info_hash)
		hashed = urllib.quote_plus(hashed)
		encoding = urllib.urlencode({ 'infohash' : self.info_hash})
		url = tracker + "?info_hash=" + hashed
		try:
			txt = urlopen(url, timeout=10).read()
		except URLError:
			if(retry_attempt):
				return None
			else:
				print("Error: Scrape of " + self.URL + ". Trying again...")
				return self._scrape_http(True)
		data = bencode.bdecode(txt)
		return (util.dict_find("complete", data), util.dict_find("downloaded", data), util.dict_find("incomplete", data))


	def _announce_http(self, num_want, retry_attempt=False):
		tracker = self.serv_type + "://" + self.URL + ":" + str(self.port) +"/announce"
		hashed = binascii.a2b_hex(self.info_hash)
		hashed = urllib.quote_plus(hashed)
		url = tracker + "?info_hash=" + hashed + "&peer_id=12345678987654321234&port=" + str(self.port) + "&uploaded=0&downloaded=0&left=0&compact=1&event=started&numwant=" + str(num_want)
		try:
			txt = urlopen(url, timeout=10).read()
		except URLError:
			if(retry_attempt):
				print("Error, could not open URL " + url)
				return None
			else:
				print("Error, cannot open URL " + url + ". Trying again...")
				return self._announce_http(num_want, True)
		data = bencode.bdecode(txt)
		try:
			if data["failure reason"]:
				print("Error: HTTP server " + self.URL + " returned error '" + data["failure reason"] + "' on announce request.")
				return None
		except KeyError:
			pass
		peers = util.dict_find('peers', data)
		index = 0
		if(not peers == '' and (len(peers[index:(index + 4)]) == 4)):
			peer_IPs = []
			for i in range(0,num_want - 1):
				try:
					ip = socket.inet_ntoa(peers[index:(index + 4)])
				#u_port = struct.unpack(">H", res[index + 4: index + 6])
					peer_IPs.append(ip)
					index += 6
				except socket.error:
					return None
		else:
			return None
		return peer_IPs