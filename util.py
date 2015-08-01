"""
Author: Dylan Feldman

Utility functions for tracker scraper program
"""
import re
import requests
from urlparse import urlparse, urlunsplit
import geoip2.database

#Set up geoip database reader
ip_reader = geoip2.database.Reader('IP/City.mmdb')

#Parse tracker url and return tuple as follows: (tracker_type (UDP or HTTP), tracker_url, tracker_port)
def parse_tracker_url(URL):
    #re_match = re.match( r'(.*)://(.*):(.*)/.*', URL, re.I)
    #return (re_match.group(1), re_match.group(2), re_match.group(3))
    URL = URL.lower()
    URL_parsed = urlparse(URL)
    netloc = URL_parsed.netloc.split(":")
    return (URL_parsed.scheme, netloc[0], netloc[1])
    

#Get torrent name from torrentz.me NOT WORKING
def get_torrent_name(infohash):
    url = "http://torrentz.me/" + infohash
    p = urlopen(url)
    page = p.read()
    c = re.compile(r'<h2><span>(.*?)</span>')
    return c.search(page).group(1)


#Get geolocation from freegeoip.net and return json object
def get_geolocation_for_ip(ip):
    location = ip_reader.city(ip)
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


    #GEO_IP_url = 'http://freegeoip.net/json/'
    #url = '{}/{}'.format(GEO_IP_url, ip)
    #response = requests.get(url)
    #response.raise_for_status()
    #return response.json()
