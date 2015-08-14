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


def tracker_list_init(torrent):
    tracker_list = []
    try:
        for URL in torrent["announce-list"]:
            URL = URL[0]
            tracker_type, tracker_address, port = parse_tracker_url(URL)#"open.demonii.com"
        #tracker_type, tracker_address, port = util.parse_tracker_url("http://mgtracker.org:2710/announce")#"open.demonii.com"
            tracker_list.append(tracker.Tracker(hashlib.sha1(bencode.bencode(torrent['info'])).hexdigest(), tracker_type, tracker_address, port))
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

    #re_match = re.match( r'(.*)://(.*):(.*)/.*', URL, re.I)
    #return (re_match.group(1), re_match.group(2), re_match.group(3))
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


#Get geolocation from freegeoip.net and return json object
def get_geolocation_for_ip(ip):
    try:
        location = ip_reader.city(ip)
    except geoip2.errors.AddressNotFoundError:
        print("Error: " + ip + " not in database")
        return None
    #print(ip_anon.name_by_addr(ip))
    if (location.city.name is None) or ("\\" in location.city.name):
        if location.country.name is None:
            return ("Unknown", "Unknown")
        else:
            return (location.country.name, "Unknown")
    else:
        if location.country.name is None:
            return ("Unknown", location.city.name)
        else:
            return (location.country.name, location.city.name)

