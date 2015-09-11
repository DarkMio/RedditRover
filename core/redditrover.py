# coding=utf-8
from configparser import ConfigParser
from pkg_resources import resource_filename
from time import time, sleep, strptime
from sys import exit
import pkgutil
import traceback

from praw.errors import *
import praw

import plugins
from core import logprovider
from misc import warning_filter

from core import *
from .decorators import retry


class RedditRover:
    """
    Reddit Rover object is the full framework. When initing, it reads all plugins, initializes them and starts loading
    submissions and comments from Reddit. Varying from your implementation, it will fire those submissions and comments
    to your bot. Based on the configuration setting the bot will run a maintenance and update procedure, cleaning up
    the database and rolling over submissions / comments of a plugin which requested to update from there out on.


    :ivar logger: Central bot logger.
    :vartype logger: Logger
    :ivar config: Holds a full set of configs from the configfile.
    :vartype config: ConfigParser
    :ivar responders: A list of plugins the bot is running. @TODO: Exit the bot if no plugin is found.
    :vartype responders: list
    :ivar multi_thread: The MultiThreader instance, which manages daemonic threads.
    :vartype multi_thread: MultiThreader
    :ivar delete_after: All activity older than x seconds will be cleaned up from the database.
    :vartype delete_after: int
    :ivar praw_handler: Will hold the handler to RateLimit based on OAuth / No-Auth sessions.
    :vartype praw_handler: RedditRoverHandler
    :ivar submission_poller: Anonymous reddit session for submissions.
    :vartype submission_poller: praw.Reddit
    :ivar comment_poller: Anonymous reddit session for comments.
    :vartype comment_poller: praw.Reddit
    :ivar submissions: Generator of recent submissions on Reddit.
    :vartype submissions: praw.helpers.comment_stream
    :ivar comments: Generaot of recent comments on Reddit.
    :vartype comments: praw.helpers.comment_stream
    """

    def __init__(self):
        warning_filter.ignore()
        self.logger = logprovider.setup_logging(log_level="DEBUG")
        self.read_config()
        self.multi_thread = MultiThreader()
        self.database_update = DatabaseProvider()
        self.database_cmt = DatabaseProvider()
        self.database_subm = DatabaseProvider()
        try:
            self.praw_handler = RoverHandler()
            self.load_responders()
            self.submission_poller = praw.Reddit(user_agent='Submission-Poller for several logins by /u/DarkMio',
                                                 handler=self.praw_handler)
            self.comment_poller = praw.Reddit(user_agent='Comment-Poller for several logins by /u/DarkMio',
                                              handler=self.praw_handler)
        except Exception as e:  # I am sorry linux, but ConnectionRefused Error can't be imported..
            self.logger.error("PRAW Multiprocess server does not seem to be running. "
                              "Please make sure that the server is running and responding. "
                              "Bot is shutting down now.")
            self.logger.error(e)
            self.logger.error(traceback.print_exc())
            exit(-1)
        self.delete_after = self.config.get('RedditRover', 'delete_after')
        self.submission_stream()
        self.comment_stream()
        self.lock = self.multi_thread.get_lock()
        self.multi_thread.go([self.comment_thread], [self.submission_thread], [self.update_thread])
        self.multi_thread.join_threads()

    def _filter_single_thing(self, thing, responder):
        try:
            if isinstance(thing, praw.objects.Comment):
                db = self.database_cmt
            else:
                db = self.database_subm
            b_name = responder.BOT_NAME
            if db.retrieve_thing(thing.name, b_name):
                return False
            if hasattr(thing, 'author') and type(thing.author) is praw.objects.Redditor:
                if db.check_user_ban(thing.author.name, b_name):
                    return False
                if thing.author.name == responder.session.user.name and hasattr(responder, 'SELF_IGNORE') and \
                        responder.SELF_IGNORE:
                    return False
            if hasattr(thing, 'subreddit') and db.check_subreddit_ban(thing.subreddit.display_name, b_name):
                return False
            return True
        except Exception:
            return False

    def load_responders(self):
        """Main method to load sub-modules, which are designed as a framework for multiple bots.
           This allows to abstract bots even more than what PRAW does and it's nicely handled in
           a threaded environment to do multiple tasks pretty efficient without writing a full new bot."""
        # cleaning of the list
        self.responders = list()
        # preparing the right sub path.
        package = plugins
        prefix = package.__name__ + "."

        # we're running through all
        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
            module = __import__(modname, fromlist="dummy")
            # every sub module has to have an object provider,
            # this makes importing the object itself easy and predictable.
            module_object = module.init(DatabaseProvider(), self.praw_handler)
            try:
                if not isinstance(module_object, Base):
                    raise ImportError('Module {} does not inherit from Base class'.format(
                        module_object.__class__.__name__))
                # could / should fail due to variable validation
                # (aka: is everything properly set to even function remotely.)
                module_object.integrity_check()
                self.database_update.register_module(module_object.BOT_NAME)
                self.logger.info('Module "{}" is initialized and ready.'.format(module_object.__class__.__name__))
            except Exception as e:
                # Catches _every_ error and skips the module. The import will now be reversed.
                self.logger.error(traceback.print_exc())
                self.logger.error("{}: {}".format(module_object.__class__.__name__, e))
                del module, module_object
                continue
            # If nothing failed, it's fine to import.
            self.responders.append(module_object)
        self.logger.info("Imported a total of {} object(s).".format(len(self.responders)))

    def submission_thread(self):
        """The submission thread runs down all submission from the specified sub (usually /r/all)
           Then it filters out all banned users and subreddits and then fires submissions at your plugins."""
        self.logger.info("Opened submission stream successfully.")
        for subm in self.submissions:
            self.comment_submission_worker(subm)

    def comment_thread(self):
        """The comment thread runs down all comments from the specified sub (usually /r/all)
           then filters out banned users and subreddits and fires it at your plugins."""
        self.logger.info("Opened comment stream successfully.")
        for comment in self.comments:
            self.comment_submission_worker(comment)

    def comment_submission_worker(self, thing):
        """Refactored to one big execution chain - smart enough to split comments and submissions apart."""
        for responder in self.responders:
            # Check beforehand if a subreddit or a user is banned from the bot / globally.
            if self._filter_single_thing(thing, responder):
                try:
                    self.comment_submission_action(thing, responder)
                except Forbidden:
                    name = thing.subreddit.display_name
                    self.database_subm.add_subreddit_ban_per_module(name,
                                                               responder.BOT_NAME)
                    self.logger.error("It seems like {} is banned in '{}'. The bot will ban the subreddit now"
                                      " from the module to escape it automatically.".format(responder.BOT_NAME, name))
                except NotFound:
                    pass
                except (APIException, InvalidSubmission) as e:
                    if isinstance(e, APIException) and e.error_type == 'DELETED_LINK' \
                            or isinstance(e, InvalidSubmission):
                        self.logger.debug('{} tried to comment on an already deleted resource - ignored.'.format(
                            responder.BOT_NAME))
                        pass
                except Exception as e:
                    self.logger.error(traceback.print_exc())
                    self.logger.error("{} error: {} < {}".format(responder.BOT_NAME, e.__class__.__name__, e))

    @retry(HTTPException)  # when the API fails, we're here to catch that.
    def comment_submission_action(self, thing, responder):
        if isinstance(thing, praw.objects.Submission) and thing.is_self and thing.selftext:
            responded = responder.execute_submission(thing)
        elif isinstance(thing, praw.objects.Submission) and thing.is_self:
            responded = responder.execute_titlepost(thing)
        elif isinstance(thing, praw.objects.Submission):
            responded = responder.execute_link(thing)
        else:
            responded = responder.execute_comment(thing)

        if responded:
            if isinstance(thing, praw.objects.Comment):
                self.database_cmt.insert_into_storage(thing.name, responder.BOT_NAME)
            else:
                self.database_subm.insert_into_storage(thing.name, responder.BOT_NAME)

    @retry(HTTPException, 2, 3, 1)  # Sometimes the API bugs out, we give it 2 tries, á 3 seconds
    def update_thread(self):
        """The update-thread does a lot of different tasks.
           First it loads all threads that have to update and executes the update_procedure of your plugin.
           Then it loads all unread messages of your plugin, cleans up the database and sleeps for 5 minutes."""
        while True:
            self.lock.acquire(True)
            for responder in self.responders:
                threads = self.database_update.get_all_to_update(responder.BOT_NAME)
                if threads:
                    for thread in threads:
                        self.update_action(thread, responder)
                try:
                    responder.get_unread_messages()
                except Exception as e:
                    self.logger.error(traceback.print_exc())
                    self.logger.error("{} error: {} < {}".format(responder.BOT_NAME, e.__class__.__name__, e))
            self.database_update.clean_up_database(int(time()) - int(self.delete_after))
            self.lock.release()
            # after working through all update threads, sleep for five minutes. #saveresources
            sleep(360)

    @retry(HTTPException)  # when the API bugs out, we retry it for a while, this thread has time for it anway.
    def update_action(self, thread, responder):
        # reformat the entry from the database, so we can feed it directly into the update_procedure
        thread_dict = {'thing_id': thread[0],
                       'created': strptime(thread[2], '%Y-%m-%d %H:%M:%S'),
                       'lifetime': strptime(thread[3], '%Y-%m-%d %H:%M:%S'),
                       'last_updated': strptime(thread[4], '%Y-%m-%d %H:%M:%S'),
                       'interval': thread[5]}
        self.database_update.update_timestamp_in_update(thread_dict['thing_id'], responder.BOT_NAME)
        try:
            responder.update_procedure(**thread_dict)
        except Exception as e:
            self.logger.error("{} error: {} < {}".format(responder.BOT_NAME, e.__class__.__name__, e))

    def submission_stream(self):
        """Opens a new thread, which reads submissions from a specified subreddit."""
        self.submissions = praw.helpers.submission_stream(self.submission_poller, 'all', limit=None, verbosity=0)

    def comment_stream(self):
        """Opens a new thread, which reads comments from a specified subreddit."""
        self.comments = praw.helpers.comment_stream(self.comment_poller, 'all', limit=None, verbosity=0)

    def read_config(self):
        """Reads the config."""
        self.config = ConfigParser()
        self.config.read(resource_filename('config', 'bot_config.ini'))
        self.logger.info("Configuration read and set up properly.")

if __name__ == "__main__":
    mb = RedditRover()
