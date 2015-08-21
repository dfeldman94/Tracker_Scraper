"""
Author: Dylan Feldman

Torrent object specification for tracker scraper program
"""

import util
import os

#Class for representing tracker for a torrent
class Torrent(object):
	def __init__(self, name, tracker_list):
		self.name = name
		self.tracker_list = tracker_list
		self.IPs = []
		self.geo_info = {}
		#self.connection_id=0x41727101980

	def add_tracker(self, tracker):
		self.tracker_list.append(tracker)

	def scrape_all(self):
		seeders, leechers, completed = 0,0,0
		for tracker in self.tracker_list:
			scrape_result = tracker.scrape()
			if(scrape_result):
				print("Successfully scraped " + tracker.URL)
				# vvv Summing is not correct, peers are not mutually exlusive across trackers.
				seeders, completed, leechers = seeders + scrape_result[0], completed + scrape_result[1], leechers + scrape_result[2]
				break
			else:
				print("Error: Could not scrape " + tracker.URL + ". Continuing...")
		self.seeders, self.completed, self.leechers = seeders, completed, leechers
		return (seeders, completed, leechers)

	def get_IP(self, get_all=False, num_want=50, max_attempts=3, ignore_wait=False):
		for each_tracker in self.tracker_list:
			pre_len = len(self.IPs)
			if(get_all):
				new_IPs = each_tracker.get_all_IPs(num_want, ignore_wait=ignore_wait)
				if(new_IPs):
					for each_IP in new_IPs:
						if each_IP not in self.IPs:
							self.IPs.append(each_IP)
							ip_location = util.get_geolocation_for_ip(each_IP)
							
							if not ip_location:
								continue
							loc_key = (ip_location['country'], ip_location['city'])
							if loc_key not in self.geo_info.keys():
								ip_location['n'] = 1
								self.geo_info[loc_key] = ip_location
							else:
								self.geo_info[loc_key]['n'] += 1
					print("Successfully collected " + str(len(self.IPs) - pre_len) + " new IPs from " + each_tracker.URL)
				else:
					print("Error: Could not announce to tracker " + each_tracker.URL)
			else:
				new_IPs = each_tracker.get_IPs(num_want)
				if(not (new_IPs == -1)):
					for each_IP in new_IPs:
						if each_IP not in self.IPs:
							self.IPs.append(each_IP)
							ip_location = util.get_geolocation_for_ip(each_IP)
							loc_key = (ip_location['country'], ip_location['city'])
							if not ip_location:
								continue
							if loc_key not in self.geo_info.keys():
								ip_location['n'] = 1
								self.geo_info[loc_key] = ip_location
							else:
								self.geo_info[loc_key]['n'] += 1
					print("Successfully collected " + str(len(self.IPs) - pre_len) + " new IPs from " + each_tracker.URL)
				else:
					print("Error: Could not announce to tracker " + each_tracker.URL)
		return self.IPs

	def print_details(self, geo=True, IP=False):
		try:
			print("Seeders: ", self.seeders)
			print("Leechers: ", self.leechers)
			print("Completed: ", self.completed)
		except AttributeError:
			print("Error: Torrent not scraped before printing details")
			return None
		if geo:
			#print(self.geo_info)
			for loc in self.geo_info.keys():
				formatted_line = ""
				if type(loc) is tuple:

					formatted_line = u'' + self.geo_info[loc]['country'] + ", " + self.geo_info[loc]['city']

				else:
					formatted_line = loc
				formatted_line += ": " + str(self.geo_info[loc]['n'])
				print(formatted_line)
		elif IP:
			self.print_IP()

		

	def dump_to_file(self, filename, geo=True):
		print("Dumping info to '" + filename + "'...")
		info_file = None
		try:
			info_file = open(filename, "w")
		except OSError:
			print("Error opening file '" + filename + "'\nMake sure the file name is valid, and that you have proper write permissions.")
		try:
			info_file.write("Seeders: " + str(self.seeders) + "\n")
			info_file.write("Leechers: " + str(self.leechers) + "\n")
			info_file.write("Completed: " + str(self.completed) + "\n\n\n")
		except AttributeError:
			print("Error: Torrent " + self.name + " not successfully scraped before dumping to file")
			info_file.close()
			return None
		info_file.write("location	n")
		if geo:
			#print(self.geo_info)
			for loc in self.geo_info.keys():
				formatted_line = ""
				formatted_line = u'' + self.geo_info[loc]['country'] + ", " + self.geo_info[loc]['city']
				formatted_line += ":	" + str(self.geo_info[loc]['n']) + "\n"
				info_file.write(formatted_line.encode('utf8'))
		info_file.write("\n")
		info_file.close()

	def dump_to_JSON(self, filename):
		print("Dumping info to '" + filename + "'...")
		info_file = None
		try:
			info_file = open(filename, "w")
		except OSError:
			print("Error opening file '" + filename + "'\nMake sure the file name is valid, and that you have proper write permissions.")
		info_file.write("var point_data_json = {\"type\": \"FeatureCollection\", \"features\": [\n")
		for loc in self.geo_info.keys():
			point = util.create_point(self.geo_info[loc]['lat'], self.geo_info[loc]['long'])
			if point is None:
				continue
			info_file.write(point)
			info_file.write(", ")
		info_file.seek(-2, os.SEEK_END)
		info_file.truncate()
		info_file.write("]}")


