"""
Author: Dylan Feldman

Entry point for tracker scraper program
"""

import bencode
import hashlib
import socket
import struct   
from random import randrange #to generate random transaction_id
from urllib2 import urlopen
from contextlib import closing
import json
import time
import sys
import tracker
import re
import util
import os

import urllib
from urlparse import urlparse
import binascii
import urllib2
import torrent




#Check input arguments
if not (len(sys.argv) >= 2):
    print("Usage Error: python tscrape.py TORRENT_FILE_PATH [-I]")
    exit(1)

#Initialize Flags
ignore_wait = False
viz = False

#Parse inputs, create Tracker object
torrent_file_name = sys.argv[1]
if (len(sys.argv) > 2):
	optional_args = sys.argv[2:len(sys.argv) + 1]
	if "-i" in [c.lower() for c in optional_args]:
		ignore_wait = True
	if "-v" in [c.lower() for c in optional_args]:
		viz = True

#Open Torrent file, parse for useful info
try:
    with open(torrent_file_name, 'rb') as torrentfile:
        torrent_info = bencode.bdecode(torrentfile.read())
except IOError:
    #ERROR
    print("Error: Cannot find file " + torrent_file_name)
    exit(1)

#Create torrent object
torr = torrent.Torrent(torrent_info['info']['name'], util.tracker_list_init(torrent_info))
#tracker_type, tracker_address, port = util.parse_tracker_url(torrent_info['announce'])#"open.demonii.com"
#tracker_type, tracker_address, port = util.parse_tracker_url("http://mgtracker.org:2710/announce")#"open.demonii.com"
#track = tracker.Tracker(hashlib.sha1(bencode.bencode(torrent_info['info'])).hexdigest(), tracker_type, tracker_address, int(port), torrent_info['info']['name'])
#track = tracker.Tracker(hashlib.sha1(bencode.bencode("2c7fac7a8b18716e7209fc4ad769642deab43ae1")).hexdigest(), tracker_type, tracker_address, int(port))

  
#print(track._announce_http(10))

#print(track.scrape_http())
print("Connecting to " + torrent_info['info']['name'] + "...")
print(torr.scrape_all())
torr.get_IP(get_all=True, ignore_wait=ignore_wait)
torr.print_details()
torr.dump_to_file(torr.name + ".tsv")
if(viz):
	torr.dump_to_JSON("output.js")
	print("Starting visualization server...")
	os.system("python -m SimpleHTTPServer")


#track.connect()
#track.scrape()

#print("Requesting IPs...")
#track.get_all_IPs(ignore_wait=ignore_wait, max_attempts=100)
#track.print_details(geo=True)
#track.dump_to_file(track.name + ".info")
#print("HERE")
#track.disconnect()



