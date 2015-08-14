"""
Author: Dylan Feldman

Exception classes for tracker scraper
"""

def TimeoutError(Exception):
	def __init__(self, message, errors):

		super(ValidateError, self).__init__(message)