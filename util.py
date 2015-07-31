"""
Author: Dylan Feldman

Utility functions for tracker scraper program
"""
import re
import requests

#Parse tracker url and return tuple as follows: (tracker_type (UDP or HTTP), tracker_url, tracker_port)
def parse_tracker_url(URL):
    re_match = re.match( r'(.*)://(.*):(.*)/.*', URL, re.I)
    return (re_match.group(1), re_match.group(2), re_match.group(3))

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
