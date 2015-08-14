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

	def get_IP(self, get_all=False, num_want=50, max_attempts=3):
		for tracker in self.tracker_list:
			if(get_all):
				self.IPs.extend(tracker.get_all_IPs(max_attempts))
			else:
				self.IPs.extend(tracker.get_IPs(num_want))
		return self.IPs

	def print_details(self):
		for each_tracker in self.tracker_list:
			print("Details for " + self.name + " on Tracker " + each_tracker.URL)
			each_tracker.print_details(geo=True)

	def dump_to_file(self, file_name):
		info_file = None
		try:
			info_file = open(file_name, "a")
		except OSError:
			print("Error creating file '" + file_name + "'\nMake sure the file name is valid, and that you have proper write permissions.")
		for each_tracker in self.tracker_list:
			info_file.write("Details for " + self.name + " on Tracker " + each_tracker.URL)
			each_tracker.dump_to_file(file_name)



