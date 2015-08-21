"""
Author: Dylan Feldman

Utility functions for tracker scraper program
"""
import re
import requests
from urlparse import urlparse, urlunsplit
import geoip2.database
import GeoIP
import tracker
import hashlib
import bencode

#Set up geoip database reader
ip_reader = geoip2.database.Reader('IP/City.mmdb')
ip_anon = GeoIP.open('IP/IPASN.dat', GeoIP.GEOIP_STANDARD)


def tracker_list_init(torrent, listen_port=8080):
    tracker_list = []
    try:
        for URL in torrent["announce-list"]:
            URL = URL[0]
            tracker_type, tracker_address, port = parse_tracker_url(URL)#"open.demonii.com"
        #tracker_type, tracker_address, port = util.parse_tracker_url("http://mgtracker.org:2710/announce")#"open.demonii.com"
            tracker_list.append(tracker.Tracker(hashlib.sha1(bencode.bencode(torrent['info'])).hexdigest(), tracker_type, tracker_address, port, listen_port, torrent['info']['name']))
    except KeyError:
        print("Torrent has no announce-list, looking for single tracker...")
        try:
            for URL in torrent["announce"][0]:
                tracker_type, tracker_address, port = parse_tracker_url(URL)#"open.demonii.com"
                #tracker_type, tracker_address, port = util.parse_tracker_url("http://mgtracker.org:2710/announce")#"open.demonii.com"
                tracker_list.append(tracker.Tracker(hashlib.sha1(bencode.bencode(torrent['info'])).hexdigest(), tracker_type, tracker_address, port))
        except KeyError:
            print("Error: cannot find announce server for torrent " + torrent['info'])
    return tracker_list

def dict_find(item, d):
    if item in d:
        return d[item]
    for k in d.keys():
        if isinstance(d[k], list) or isinstance(d[k], dict):
            for i in d[k]:
                return dict_find(item, d[k])


#Parse tracker url and return tuple as follows: (tracker_type (UDP or HTTP), tracker_url, tracker_port)
def parse_tracker_url(URL):
    URL = URL.lower()
    URL_parsed = urlparse(URL)
    if (URL_parsed.scheme in ["http", "https"]):
        return (URL_parsed.scheme, URL_parsed.netloc, 80) #HTTP is always port 80
    netloc = URL_parsed.netloc.split(":")
    return (URL_parsed.scheme, netloc[0], int(netloc[1]))
    

#Get torrent name from torrentz.me NOT WORKING
def get_torrent_name(infohash):
    url = "http://torrentz.me/" + infohash
    p = urlopen(url)
    page = p.read()
    c = re.compile(r'<h2><span>(.*?)</span>')
    return c.search(page).group(1)


#Get geolocation from freegeoip.net and return j
def get_geolocation_for_ip(ip):
    try:
        location = ip_reader.city(ip)
    except geoip2.errors.AddressNotFoundError:
        print("Error: " + ip + " not in database")
        return None
    loc = {}
    loc["ip"] = ip
    loc["city"] = "Unknown" if (location.city.name is None or "\\" in location.city.name) else location.city.name
    loc["country"] = "Unknown" if (location.country.name is None or "\\" in location.country.name) else location.country.name #// = unicode name. deal with it!
    loc["lat"] = "Unknown" if (location.location.latitude is None) else location.location.latitude
    loc["long"] = "Unknown" if (location.location.longitude is None) else location.location.longitude
    loc["n"] = 0
    return loc

def create_point(lat, longitude, peers):
    if lat == "Unknown" or longitude == "Unknown":
        return None
    return "{\"type\":\"Feature\",\"geometry\":{\"type\":\"Point\",\"coordinates\": [" + str(longitude) + ", " + str(lat) +"]}, \"properties\": {\"peers\":"+ str(peers) +"}}\n"