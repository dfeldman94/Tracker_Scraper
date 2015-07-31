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



#Check input arguments
if not (len(sys.argv) == 2):
    print("Usage Error: python tscrape.py TORRENT_FILE_PATH")
    exit(1)

#Parse inputs, create Tracker object
torrent_file_name = sys.argv[1]
try:
    with open(torrent_file_name, 'rb') as torrentfile:
        torrent = bencode.bdecode(torrentfile.read())
except IOError:
    #ERROR
    print("Error: Cannot find file " + torrent_file_name)
    exit(1)


tracker_type, tracker_address, port = util.parse_tracker_url(torrent['announce'])#"open.demonii.com"
track = tracker.Tracker(hashlib.sha1(bencode.bencode(torrent['info'])).hexdigest(), tracker_type, tracker_address, int(port))

print("Connecting to " + tracker_address + "...")
track.connect()
track.scrape()
track.print_details()

print("Requesting IPs...")
track.req_IPs(5)
track.print_details(geo=True)
#print("HERE")
track.disconnect()



