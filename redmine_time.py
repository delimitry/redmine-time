#!/usr/bin/env python
#-*- coding:utf-8 -*-
#----------------------------------------------------------------------- 
# Author: delimitry
#-----------------------------------------------------------------------

import urllib
import urllib2
import os
import re
import sys
from urllib2 import Request, build_opener, HTTPCookieProcessor, HTTPHandler
import cookielib
import ConfigParser

class http_client(object):

	def __init__(self, proxy=None, user_agent='Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3'):
		self.cookie_handler   = urllib2.HTTPCookieProcessor(cookielib.CookieJar())
		self.redirect_handler = urllib2.HTTPRedirectHandler()
		self.http_handler     = urllib2.HTTPHandler()
		self.https_handler    = urllib2.HTTPSHandler()

		self.opener = urllib2.build_opener(self.http_handler,
										   self.https_handler,
										   self.cookie_handler,
										   self.redirect_handler)

		if proxy:
			self.proxy_handler = urllib2.ProxyHandler(proxy)
			self.opener.add_handler(self.proxy_handler)

		self.opener.addheaders = [('User-agent', user_agent),
								  ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
								  ('Accept-Language', 'en-us,en,;q=0.5'),
								  ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*,q=0.7')]

	def request(self, url, params={}, timeout=60):
		if params:
			params = urllib.urlencode(params)
			html = self.opener.open(url, params, timeout)
		else:
			html = self.opener.open(url)
		return html.read()

def get_today_and_month_time(url, login, password):
	try:
		# init http client and get login page data
		client = http_client()		
		data_login = client.request(url + '/login')
	except Exception, ex:
		print 'Failed to open login page:', ex	
		return ''

	# init regexp pattern for token
	token_pattern = re.compile('''authenticity_token" type="hidden" value="([0-9a-f]{40})"''')
	token_matches = re.findall(token_pattern, data_login)
	if len(token_matches) == 0: return ''
	# set authenticity token from match
	authenticity_token = token_matches[0]

	try:
		# try to login using params	
		login_result = client.request(url + '/login', { 'authenticity_token' : authenticity_token, 'username' : login, 'password' : password, 'login' : 'Login »' })
		if 'Invalid user or password' in login_result: raise Exception('Invalid username or password')
	except Exception, ex:
		print 'Login failed:', ex
		return ''

	# init regexp pattern for spent time
	pattern = re.compile('''<td>%s</td>[^>]*<td class="hours"><span class="hours hours-int">(\d+)</span><span class="hours hours-dec">\.(\d+)</span></td>''' % (login))

	# get month time
	request_month_str = '/time_entries/report?criterias[]=member&criterias[]=&period_type=1&period=current_month&from=&to=&columns=month&authenticity_token=%s' % (authenticity_token)
	data_month_time = client.request(url + request_month_str)
	month_time_list = re.findall(pattern, data_month_time)

	# get today time
	request_today_str = '/time_entries/report?criterias[]=member&criterias[]=&period_type=1&period=today&from=&to=&columns=month&authenticity_token=%s' % (authenticity_token)
	data_today_time = client.request(url + request_today_str)
	today_time_list = re.findall(pattern, data_today_time)

	# prepare results
	result = ''
	if today_time_list and len(today_time_list) > 0:
		today_time = today_time_list[0]		
		result += 'Today time: %s.%s\n' % (today_time[0], today_time[1])
	if month_time_list and len(month_time_list) > 0:
		month_time = month_time_list[0]
		result += 'Month time: %s.%s\n' % (month_time[0], month_time[1])
	return result

def main():
	# read configuration data from a file
	config = ConfigParser.ConfigParser()
	config.read(sys.path[0] + '/config.dat')

	# init values from information section
	url = config.get('information', 'url')
	login = config.get('information', 'login')
	password = config.get('information', 'password')

	# get user time
	result = get_today_and_month_time(url, login, password)
	if result != '': print result

if __name__ == '__main__':
	main()