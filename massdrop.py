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
from BeautifulSoup import BeautifulSoup
from time import time, sleep

class multithread(object):

	def __init__(self):
		self.running = True
		self.threads = []

		self.r = praw.Reddit(user_agent='MASSDROP guest link poster')
		self.r.login()
		self.subreddit = 'all'
		self.now = int(time())
		# best handling without formatting is to not format it.
		self.comment = "Hi, I am /u/MassdropBot.\n\nI've detected that you posted a great Massdrop offer but unfortunately unregistered people cannot see it. I am here to fix that:\n\n%s\n\n---\n\n^This ^is ^a ^bot ^and ^won't ^answer ^to ^mails. ^Mail ^the ^[[Botowner](http://www.reddit.com/message/compose/?to=DarkMio&amp;subject=BotReport)] ^instead. ^v0.4 ^| ^[Changelog](http://redd.it/29f2ah)"
		self.comment_multiple = "Hi, I am /u/MassdropBot.\n\nI've detected that you posted some great Massdrop offers but unfortunately unregistered people cannot see it. I am here to fix that:\n\n%s\n\n---\n\n^This ^is ^a ^bot ^and ^won't ^answer ^to ^mails. ^Mail ^the ^[[Botowner](http://www.reddit.com/message/compose/?to=DarkMio&amp;subject=BotReport)] ^instead. ^v0.4 ^| ^[Changelog](http://redd.it/29f2ah)"

	def comment_stream(self):
		"""Loads ALL comments from all threads. We watch you fappin'."""
		while True:

			try:
				comment_stream = praw.helpers.comment_stream(self.r, self.subreddit, limit=None, verbosity=0)
				log.info("Opened comment stream successfully.")
				while self.running == True:
					comment = next(comment_stream) # Retrieve the next comment

					if (	"massdrop.com/buy" in comment.body
						and not check(comment.id)
						and not str(comment.author) == 'MassdropBot'
						): # so, we found at least one massdrop-buy link, let's do this!
						linklist = []

						# seach for link.
						link = re.findall("(?P<url>https?:\/\/(?:www\.)?massdrop\.com\/buy\/[^\s)]*)", comment.body)

						# returns a list with all Massdrop link in one comment.
						for item in link:
							item = str(item)
							if not "mode=guest_open" in item:
								query = ('?' in item and '&') or '?'
								guest_link = item+query+"mode=guest_open"
								# load a title, so we can link what is what.
								try:
									title = BeautifulSoup(urllib2.urlopen(guest_link)).title.string
									title = title.strip(' - Massdrop')+": "
								except:
									title = ""
								linklist.append("\n\n"+title+guest_link)


						# joins all links to a string, so we can use it easily in our comment without overcomplicating things.
						string_links = ''.join(map(str, linklist))

						# make a dynamic response, based on the amount of links posted.
						reply = (len(linklist) > 1 and self.comment_multiple % string_links) or self.comments % string_links

						# and reply to it - needs a retry feature soon
						log.info("Found a comment with ID %s, replying and storing." % comment.id)
						comment.reply(reply)
						add(comment.id)

			except:
				log.info("Comment stream broke. Retrying in 60.")
				sleep(60)
				pass


	def submission_stream(self):
		"""Checks all submissions. Either they're link.posts or self.posts. Either way, we catch both."""
		while True:

			try:
				submission_stream = praw.helpers.submission_stream(self.r, self.subreddit, limit=None, verbosity=0)
				log.info("Opened submission stream successfully.")
				while self.running == True:
					submission = next(submission_stream) # retrieve the next submission

					for data in [submission.url, submission.selftext]:
					
						if (	"massdrop.com/buy" in data # is massdrop we can use?
							and not check(submission.id) # is it already worked (for quick bot reboots.)
							):	


							if not "reddit" in submission.url:

								query = ('?' in submission.url and "&") or "?"
								guest_link = submission.url+query+"mode=guest_open"
								try:
									# load the website title
									title = BeautifulSoup(urllib2.urlopen(guest_link)).title.string
									title = title.strip(' - Massdrop')+": "
								except:
									title = ""
								string_link = "\n\n"+title+guest_link

								reply = self.comment % string_link

								# it will be only one link, since link.posts can only hold one.
								log.info("Found a link.post with ID %s, adding comment and storing." % submission.id)
								submission.add_comment(reply)
								add(submission.id)


							elif submission.selftext:
								linklist = []
								# seach for link & returns a list with all links
								link = re.findall("(?P<url>https?:\/\/(?:www\.)?massdrop\.com\/buy\/[^\s)]*)", submission.selftext)

								for item in link:
									item = str(item)
									if not "mode=guest_open" in item:
										query = ('?' in item and '&') or '?'
										guest_link = item+query+"mode=guest_open"
										# load a title, so we can link what is what.
										try:
											title = BeautifulSoup(urllib2.urlopen(guest_link)).title.string
											title = title.strip(' - Massdrop')+": "
										except:
											title = ""
										linklist.append("\n\n"+title+guest_link)


								# joins all links to a string, so we can use it easily in our comment without overcomplicating things.
								string_links = ''.join(map(str, linklist))

								# make a dynamic response, based on the amount of links posted.
								reply = (len(linklist) > 1 and self.comment_multiple % string_links) or self.comment % string_links
								
								log.info("Found a self.post with ID %s, adding comment and storing." % submission.id)
								submission.add_comment(reply)
								add(submission.id)

			except:
				log.info("Submission stream broke. Retrying in 60.")
				sleep(60)
				pass
			

	def database_cleaner(self):
		"""Cleans up the database, which contains worked-through IDs."""
		while self.running == True:

			deleteme = cur.execute("SELECT * FROM reddit WHERE time + 86400 < %s" % self.now)
			i = 0
			if deleteme:
				for i, entry in enumerate(cur.fetchall()):
					cur.execute("DELETE FROM reddit WHERE id = '%s'" % entry[1])
					i += 0
				i > 0 and log.info("Cleaned %s entries from the database." % i)

			sleep(6000)


	def close(self):
		db.close()
		log.error("CRITICAL ERROR:")
		log.error(traceback.print_exc())
		log.info("Established connection to database was closed.")
		raise SystemExit


	#def get_user_input(self):
	#	while True:
	#		x = raw_input("Enter 'e' for exit: ")
	#		if x.lower() == 'e':
	#			self.running = False
	#			break


	def go(self):
		t1 = threading.Thread(target=self.comment_stream)
		t2 = threading.Thread(target=self.submission_stream)
		t3 = threading.Thread(target=self.database_cleaner)
		# Make threads daemonic, i.e. terminate them when main thread
		# terminates. From: http://stackoverflow.com/a/3788243/145400
		t1.daemon = True
		t2.daemon = True
		t3.daemon = True
		t1.start()
		t2.start()
		t3.start()
		self.threads.append(t1)
		self.threads.append(t2)
		self.threads.append(t3)


def join_threads(threads):
	"""
	Join threads in interruptable fashion.
	From http://stackoverflow.com/a/9790882/145400
	"""
	for t in threads:
		while t.isAlive():
			t.join(5)


def check(ID):
	check = cur.execute('SELECT id FROM reddit WHERE id = "%s" LIMIT 1' % ID)
	for line in check:
		sleep(10)
		if line:
			return True

def add(ID):
	cur.execute('INSERT INTO reddit (time, id) VALUES ("%s", "%s")' % (int(time()), ID))



if __name__ == "__main__":

	# SET UP LOGGER
	logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%X', level=logging.INFO)
	log = logging.getLogger('dd')

	# SET UP DATABASE
	db = sqlite3.connect('massdrop.db', check_same_thread=False, isolation_level=None)
	cur = db.cursor()

	t = multithread()
	t.go()
	try:
		join_threads(t.threads)
	except KeyboardInterrupt:
		log.info("Stopping process entirely.")
		db.close() # you can't close it enough, seriously.
		log.info("Established connection to database was closed.")