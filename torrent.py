"""
Author: Dylan Feldman

Torrent object specification for tracker scraper program
"""



#Class for representing tracker for a torrent
class Torrent(object):
	def __init__(self, name, tracker_list):
		self.name = name
		self.tracker_list = tracker_list
		self.IPs = []
		#self.connection_id=0x41727101980
	def add_tracker(self, tracker):
		self.tracker_list.append(tracker)
	def scrape_all(self):
		seeders, leechers, completed = 0,0,0
		for tracker in self.tracker_list:
			scrape_result = tracker.scrape()
			seeders, completed, leechers = seeders + scrape_result[0], completed + scrape_result[1], leechers + scrape_result[2]
		return (seeders, completed, leechers)
	def get_IP(self, all=False, num_want=50, max_attempts=3):
		for tracker in self.tracker_list:
			if(all):
				self.IPs.extend(tracker.get_all_IPs(max_attempts))
			else:
				self.IPs.extend(tracker.get_IPs(num_want))
		return self.IPs


