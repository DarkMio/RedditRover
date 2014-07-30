# This code is sloppy and just retries itself without printing any error.
# This works well for a hosted python server, but shouldn't be used on a
# dev-machine, since you will get no errors.
# This bot usually gets after a few hours for a few seconds in trouble,
# restarting one of the streams. That is a connection-error of reddit,
# just ignore it.
# Have fun.


import praw
import datetime
import random
import sqlite3
import threading
import re
import logging
import traceback
import urllib2
import argparse
import simplejson
import pprint


from BeautifulSoup import BeautifulSoup
from time import time, sleep



class linkfix(object):
	'''We're making sure before what kind of link we're talking about'''


	def __init__(self):
		self.comment = "Hi, I am /u/MassdropBot.\n\nI've detected that you posted a great Massdrop offer but unfortunately unregistered people cannot see it. I am here to fix that:\n\n%s"
		self.comment_multiple = "Hi, I am /u/MassdropBot.\n\nI've detected that you posted some great Massdrop offers but unfortunately unregistered people cannot see it. I am here to fix that:\n\n%s"
		self.subreddit = "Link for the interested:%s"
		self.subreddit_multiple = "Links for the interested:%s"
		self.gfy_comment = "OP posted a giant.gfycat.com link, which means more bandwidth and choppy gifs instead of jiffy gfys. [Read more about it here.](http://gfycat.com/about)\n\n%s"
		self.gfy_comment_multiple = "OP posted some giant.gfycat.com links, which means more bandwidth and choppy gifs instead of jiffy gfys. [Read more about it here.](http://gfycat.com/about)\n\n%s"
		
		self.disclaimer = "\n\n---\n\n^This ^is ^a ^bot ^and ^won't ^answer ^to ^mails. ^Mail ^the ^[[Botowner](http://www.reddit.com/message/compose/?to=DarkMio&amp;subject=BotReport)] ^instead. ^v0.4 ^| ^[Changelog](http://redd.it/29f2ah)"
		self.r = praw.Reddit(user_agent='Subreddit Data Puller from /u/DarkMio for a Linkfix-Object')


	def massdrop(self, textbody):
		'''Processes Massdrop-Links, makes them nice and returns a full response for reddit.'''
		# create an empty list to fill
		linklist = []
		reply = None
		# seach for multiple links.
		links = re.findall("(?P<url>https?:\/\/(?:www\.)?massdrop\.com\/buy\/[^\s)]*)", textbody)

		# returns a list with all Massdrop link in one comment.
		for item in links:
			item = str(item)
			if not "mode=guest_open" in item:
				query = ('?' in item and '&') or '?'
				guest_link = item+query+"mode=guest_open"
				guest_link = guest_link.replace('amp;', '')
				# load a title, so we can link what is what.
				try:
					title = BeautifulSoup(urllib2.urlopen(guest_link)).title.string
					title = title.replace(' - Massdrop', '')+": "
				except:
					title = ''
				linklist.append("\n\n"+title+guest_link)


		if len(linklist) > 0:
			# joins all links to a string, so we can use it easily in our comment without overcomplicating things.
			string_links = ''.join(map(str, linklist))
			# build a nice reply
			reply = (len(linklist) > 1 and self.comment_multiple % string_links) or self.comment % string_links

		if reply:
			return reply+self.disclaimer
		else:
			return


	def subreddit_name(self, title, subreddit, link):
		'''Processes titles for subreddits that got mentioned. Also filters bigger subreddits.'''
		carebox = []
		reply = None
		

		subreddits = re.findall("\s(/?[rR]/[A-Za-z0-9][^\s\].,)]*)", " "+title)
		for line in subreddits:
			line = str(line)
			if not line[0] == '/':
				line = '/'+line

			# let's try if it is a real subreddit - will fail if not
			sub_name = str(line.split('/r/')[1]).lower()
			if not sub_name == str(subreddit).lower() and not sub_name in link.lower():
				try:
					# v this will fail if it is an invalid subreddit
					sub_pointer = self.r.get_subreddit(sub_name, fetch=True)

					if sub_pointer.subscribers < 100000: # we don't care about the top 100 subreddits
						description = str(sub_pointer.public_description)
						description = (len(description) > 75 and description[:75] + '[...]') or description # don't print meters of sub-description
						nsfw = (sub_pointer.over18 and ' [**NSFW**]') or '' # is it a nsfw subreddit?

						carebox.append('\n\n'+line+nsfw+': '+description)
				except:
					pass
					#log.debug(traceback.print_exc())


		if len(carebox) > 0:
			string_carebox = ''.join(map(str, carebox))
			reply = (len(carebox) > 1 and self.subreddit_multiple % string_carebox) or self.subreddit % string_carebox

		if reply:
			return reply+self.disclaimer
		else:
			return


	def gfycat(self, textbody):
		'''Finds giant.gfycat-links and returns to the original MP4 / WebM link.'''
		carebox = []
		reply = None

		gfycats = re.findall("https?:\/\/giant\.gfycat\.com\/(\w*)", textbody)
		for line in gfycats:
			line = str(line)
			json = 'http://gfycat.com/cajax/get/'+line
			line = 'http://gfycat.com/'+line
			try:		
				# load the meta data of that GFY
				gfyjson = simplejson.load(urllib2.urlopen(json))
				gfyItem = gfyjson['gfyItem']
				
				# make a size-comparison and load the titlse
				size =+ round(1.0 * gfyItem['gifSize'] / gfyItem['mp4Size'], 1)
				if gfyItem['title'] == None:
					gfystring = line
				else:
					gfystring = "[%s](%s)" % (gfyItem['title'], line)
				#print "OP posted a giant.gfycat.com link, which means more bandwidth and choppy gifs instead of jiffy gfys. [Read more about it here.](http://gfycat.com/about)\n\n---\n"
				if len(gfycats) == 1:
					carebox.append("---\n\nThe ~%s times smaller gfycat: %s\n\n" % (size, gfystring))
				else:
					carebox.append("---\n\n%s\n\n" % gfystring)
				# check if gfycat already has an reddit-entry - and load it with praw.
				# we can do that in the obj, since we need a reddit-instance here anyway aswell.
				if gfyItem['redditId']: # and len(gfycats) == 1:
					gfysub = self.r.get_submission(submission_id=gfyItem['redditId'])
					#pprint.pprint(vars(gfysub))
					carebox.append('Original submission: (%s%% Upvotes) [%s](%s)\n\n' % (gfysub.upvote_ratio*100, gfysub.title, gfysub.short_link))
					#print self.disclaimer

			except:
				traceback.print_exc()
				title = ""
			#carebox.append('\n\n'+title+line)

		if len(carebox) > 0:
			init_strig = "OP posted a giant.gfycat.com link, which means more bandwidth and choppy gifs instead of jiffy gfys. [Read more about it here.](http://gfycat.com/about)"
			
			# This entire section is super ugly and needs some rework. There has to be some method to generate a nice
			# string in one go, instead of doing it in the for-loop AND here. Ofc there is, but - well - I am lazy.
			if len(gfycats) > 1:
				string_box = "They're avg. ~"+str(size / len(gfycats))+" times smaller than the linked gifs.\n\n" + ''.join(map(str, carebox))
			else:
				string_box = ''.join(map(str, carebox))
			reply = (len(carebox) > 1 and self.gfy_comment_multiple % string_box) or self.gfy_comment % string_box
		if reply:
			return reply+self.disclaimer
		else:
			return


if __name__ == "__main__":
	# This is a test-instance to debug the object. It will try to recreate a regular
	# software-instance and run all sorts of returns. The output is just as you would
	# expect it in the real version.
	l = linkfix()

	logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%X', level=logging.INFO)
	log = logging.getLogger('dd')

	print "\n\n > Initiating Massdrop Test.\n"
	print "Single Massdrop Test:", (l.massdrop('https://www.massdrop.com/buy/potato-keycap') and "successful.") or "failed."
	print "Single Guest Massdrop Test:", (l.massdrop('https://www.massdrop.com/buy/potato-keycap?mode=guest_open') and "failed.") or "successful."
	print "Multiple Massdrop Test:", (l.massdrop('https://www.massdrop.com/buy/potato-keycap https://www.massdrop.com/buy/beyerdynamic-dt770?referer=XK9DLP') and "successful.") or "failed."
	print "Single Referer Test:", (l.massdrop('https://www.massdrop.com/buy/beyerdynamic-dt770?referer=XK9DLP') and "successful") or "failed"
	

	print "\n\n > Initiating Subreddit Name Test.\n"
	reddit = (l.subreddit_name('No Sub: /r/2138917230435093485039485346', 'subreddit', 'http://reddit.com/r/subreddit') and "failed.") or "successful."
	print "No Subreddit in Title:", reddit
	print "Big Subreddit Test:", (l.subreddit_name('Big sub: /r/WTF', 'subreddit', 'http://reddit.com/r/subreddit') and "failed.") or "successful."
	print "Small Subreddit Test:", (l.subreddit_name('Small sub: /r/dota2modding', 'subreddit', 'http://reddit.com/r/subreddit') and "successful.") or "failed."
	print "Multiple Subreddits:", (l.subreddit_name('Multiple subs: /r/dota2modding /r/mechanicalkeyboards', 'subreddit', 'http://reddit.com/r/subreddit') and "succesful.") or "failed."


	print "\n\n > Initiating GFYcat Test:\n"
	print "Regular GFYcat test:", (l.gfycat('http://gfycat.com/SereneHideousEft') and "failed.") or "successful."
	print "Giant.GFYcat test:", (l.gfycat('http://giant.gfycat.com/SereneHideousEft.gif') and "succesful.") or "failed."
	print "Multiple GFYcat Test:", (l.gfycat('http://giant.gfycat.com/SereneHideousEft.gif http://giant.gfycat.com/AlarmingHomelyBlackbuck.gif http://giant.gfycat.com/AnimatedGrippingCottonmouth.gif http://giant.gfycat.com/ReasonableBlushingDamselfly.gi http://giant.gfycat.com/CriminalAromaticEsok.gif http://giant.gfycat.com/InsidiousIncredibleAlpinegoat.gif http://giant.gfycat.com/DopeyFaroffIrishredandwhitesetter.gif') and "successful.") or "failed."
#
##	print l.gfycat('http://giant.gfycat.com/SereneHideousEft.gif http://giant.gfycat.com/AlarmingHomelyBlackbuck.gif http://giant.gfycat.com/AnimatedGrippingCottonmouth.gif http://giant.gfycat.com/ReasonableBlushingDamselfly.gi http://giant.gfycat.com/CriminalAromaticEsok.gif http://giant.gfycat.com/InsidiousIncredibleAlpinegoat.gif http://giant.gfycat.com/DopeyFaroffIrishredandwhitesetter.gif')
##	print l.subreddit_name('Small sub: /r/dota2modding', 'subreddit', 'http://reddit.com/r/subreddit')
##	print l.subreddit_name('Multiple subs: /r/dota2modding /r/mechanicalkeyboards', 'subreddit', 'http://reddit.com/r/subreddit')