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
import sys
import tracker

#Parse tracker url and return tuple as follows: (tracker_type (UDP or HTTP), tracker_url, tracker_port)
def parse_tracker_url(URL):
    re_match = re.match( r'(.*)://(.*):(.*)/.*', URL, re.I)
    return (re_match.group(1), re_match.group(2), re_match.group(3))

#Check input arguments
if not (len(sys.argv) == 3):
    print("Usage Error: python tscrape.py TORRENT_HASH TRACKER_URL")
    exit(1)

#Parse inputs, create Tracker object
tracker_type, tracker_address, port = parse_tracker_url(sys.argv[2])#"open.demonii.com"
track = tracker.Tracker(sys.argv[1], tracker_type, tracker_address, int(port))

track.connect()
track.scrape()
track.req_IPs()
track.print_details(True)
track.disconnect()



#Get torrent name from torrentz.me NOT WORKING
def get_torrent_name(infohash):
    url = "http://torrentz.me/" + infohash
    p = urlopen(url)
    page = p.read()
    c = re.compile(r'<h2><span>(.*?)</span>')
    return c.search(page).group(1)


#Get geolocation from freegeoip.net and return json object
def get_geolocation_for_ip(ip):
    GEO_IP_url = 'http://freegeoip.net/json/'
    url = '{}/{}'.format(GEO_IP_url, ip)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

