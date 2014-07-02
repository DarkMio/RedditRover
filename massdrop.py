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
from time import time, sleep
import sqlite3
import threading
import re
import logging
import traceback


class threading(object):

	def __init__(self):
		self.running = True
		self.threads = []

		self.r = praw.Reddit(user_agent='MASSDROP guest link poster')
		self.r.login()
		self.subreddit = 'all'
		self.now = int(time())
		# best handling without formatting is to not format it.
		self.comment = "Hi, I am /u/MassdropBot.\n\nI've detected that you posted a great Massdrop offer but unfortunately unregistered people cannot see it. I am here to fix that:\n\n%s\n\n---\n\n^This ^is ^a ^bot ^and ^won't ^answer ^to ^mails. ^Mail ^the ^[[Botowner](http://www.reddit.com/message/compose/?to=DarkMio&amp;subject=BotReport)] ^instead. ^v0.2 ^| ^[Changelog](http://redd.it/29f2ah)"


	def comment_stream(self):
		"""Loads ALL comments from all threads. We watch you fappin'."""
		while True:

			try:
				comment_stream = praw.helpers.comment_stream(self.r, self.subreddit, limit=None, verbosity=0)
				log.info("Opened comment stream successfully.")
				while self.running == True:
					comment = next(comment_stream) # Retrieve the next comment
					if (	"massdrop.com/buy" in comment.body
						and not "?mode=guest_open" in comment.body
						and not check(comment.id)
						and not submission.author == 'MassdropBot'
						):


						# seach for link.
						link = re.search("(?P<url>https?://[^\s]+)", comment.body).group("url")
						# check if there is a website-query in the link
						query = ('?' in link and "&") or "?"
						link = link+query+"mode=guest_open"
						log.info("Found a comment with ID %s, replying and storing." % comment.id)

						comment.reply(self.comment % link)
						add(comment.id)

			except:
				pass


	def submission_stream(self):
		"""Checks all submissions. Either they're link.posts or self.posts. Either way, we catch both."""
		while True:

			try:
				submission_stream = praw.helpers.submission_stream(self.r, self.subreddit, limit=None, verbosity=0)
				log.info("Opened submission stream successfully.")
				while self.running == True:
					submission = next(submission_stream) # retrieve the next submission

					for data in [submission.title, submission.url, submission.selftext]:
					
						if (	"massdrop.com/buy" in data # is massdrop we can use?
							and not "?mode=guest_open" in data # is not already guest-link?
							and not check(submission.id) # is it already worked (for quick bot reboots.)
							and not submission.author == 'MassdropBot' # don't spam yourself, ty
							):	


							if not "reddit" in submission.url:

								query = ('?' in submission.url and "&") or "?"
								link = submission.url+query+"mode=guest_open"
								log.info("Found a link.post with ID %s, adding comment and storing." % submission.id)

								submission.add_comment(self.comment % link)
								add(submission.id)


							elif submission.selftext:

								link = re.search("(?P<url>https?://[^\s]+)", submission.selftext).group("url")
								query = ('?' in link and "&") or "?"
								link = link+query+"mode=guest_open"
								log.info("Found a self.post with ID %s, adding comment and storing." % submission.id)

								submission.add_comment(self.comment % link)
								add(submission.id)
			except:
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
	cur.execute('INSERT INTO reddit (time, id) VALUES ("%s", "%s")' % (self.now, ID))



if __name__ == "__main__":

	# SET UP LOGGER
	logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%X', level=logging.INFO)
	log = logging.getLogger('dd')

	# SET UP DATABASE
	db = sqlite3.connect('massdrop.db', check_same_thread=False, isolation_level=None)
	cur = db.cursor()

	t = threading()
	t.go()
	try:
		join_threads(t.threads)
	except KeyboardInterrupt:
		log.info("Stopping process entirely.")
		db.close() # you can't close it enough, seriously.
		log.info("Established connection to database was closed.")