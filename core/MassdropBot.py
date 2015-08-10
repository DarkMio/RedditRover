from configparser import ConfigParser
from os import path, popen
from time import time, sleep, strptime
from praw.handlers import MultiprocessHandler
from sys import exit
from praw.errors import Forbidden, NotFound
import praw
import core.filtering as filtering
import pkgutil

from core import LogProvider
from core.MultiThreader import MultiThreader
from core.DatabaseProvider import DatabaseProvider
from misc import warning_filter
from core.BaseClass import Base


class MassdropBot:
    logger = None  # Logging Session with full console setup.
    config = None  # Holds later a full set of configs from ConfigParser.
    users = None  # Holds usernames
    passwords = None  # Holds passwords within
    responders = None  # Keeps track of all responder objects
    multi_thread = None  # Reference to MultiThreader, which ... does the threading.
    database = None  # Reference to the DatabaseProvider
    delete_after = None  # All activity older than x seconds will be cleaned from the database.

    praw_handler = None  # Will hold the handler to connect to the praw-multiprocess server.
    submission_poller = None  # Anonymous reddit session for submissions.
    comment_poller = None  # Anonymous reddit session for comments.
    submissions = None  # Kinda list of submissions which the threads work through
    comments = None  # Same applies here, the comments are like a list, another thread runs through them

    def __init__(self):
        warning_filter.ignore()
        self.logger = LogProvider.setup_logging(log_level="DEBUG")
        self.read_config()
        self.multi_thread = MultiThreader()
        self.database = DatabaseProvider()
        try:
            self.load_responders()
            self.praw_handler = MultiprocessHandler()
            self.submission_poller = praw.Reddit(user_agent='Submission-Poller for several logins by /u/DarkMio',
                                                 handler=self.praw_handler)
            self.comment_poller = praw.Reddit(user_agent='Comment-Poller for several logins by /u/DarkMio',
                                              handler=self.praw_handler)
        except Exception as e:  # I am sorry linux, but ConnectionRefused Error can't be imported..
            self.logger.error("PRAW Multiprocess server does not seem to be running. "
                              "Please make sure that the server is running and responding. "
                              "Bot is shutting down now.")
            self.logger.error(e)
            exit(-1)
        self.delete_after = self.config.get('REDDIT', 'delete_after')
        self.submission_stream()
        self.comment_stream()
        self.lock = self.multi_thread.get_lock()
        self.multi_thread.go([self.comment_thread], [self.submission_thread], [self.update_thread])
        self.multi_thread.join_threads()

    def load_responders(self):
        """Main method to load sub-modules, which are designed as a framework for multiple bots.
           This allows to abstract bots even more than what PRAW does and it's nicely handled in
           a threaded environment to do multiple tasks pretty efficient without writing a full new bot."""
        # cleaning of the list
        self.responders = list()
        # preparing the right sub path.
        package = filtering
        prefix = package.__name__ + "."

        # we're running through all
        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
            module = __import__(modname, fromlist="dummy")
            # every sub module has to have an object provider,
            # this makes importing the object itself easy and predictable.
            module_object = module.init(self.database)
            try:
                if not isinstance(module_object, Base):
                    raise ImportError('Module {} does not inherit from Base class'.format(
                        module_object.__class__.__name__))
                # could / should fail due to variable validation
                # (aka: is everything properly set to even function remotely.)
                module_object.integrity_check()
                self.database.register_module(module_object.BOT_NAME)
                self.logger.info('Module "{}" is initialized and ready.'.format(module_object.__class__.__name__))
            except AssertionError as e:
                # Catches the error and skips the module. The import will now be reversed.
                self.logger.error("{}: {}".format(module_object.__class__.__name__, e))
                del module, module_object
                continue
            # If nothing failed, it's fine to import.
            self.responders.append(module_object)
        self.logger.info("Imported a total of {} object(s).".format(len(self.responders)))

    def print_submissions(self):
        """Prints one recent submission and one recent comment object."""
        from pprint import pprint

        for sub in self.submissions:
            pprint(vars(sub))
            break
        for cmt in self.comments:
            pprint(vars(cmt))
            break

    def submission_thread(self):
        self.logger.info("Opened submission stream successfully.")
        for submission in self.submissions:
            for responder in self.responders:
                self.lock.acquire(True)
                # Check beforehand if a subreddit or a user is banned from the bot / globally.
                if self.database.check_if_subreddit_is_banned(submission.subreddit.display_name, responder.BOT_NAME) \
                   and self.database.check_if_user_is_banned(submission.author.name, responder.BOT_NAME): continue

                if not self.database.get_thing_from_storage(submission.id, responder.BOT_NAME):
                    try:
                        if submission.is_self and submission.selftext:
                            responded = responder.execute_submission(submission)
                        elif submission.is_self:
                            responded = responder.execute_titlepost(submission)
                        else:
                            responded = responder.execute_link(submission)

                        # a responder should return with true of false, so we can manage the database for it here.
                        # reminder: writing on multiple threads is bad, reading is always fine.
                        if responded:
                            self.database.insert_into_storage(submission.name, responder.BOT_NAME)

                    except Forbidden:
                        name = submission.subreddit.display_name
                        self.database.add_subreddit_ban_per_module(name,
                                                                   responder.BOT_NAME)
                        self.logger.error("It seems like this bot is banned in '{}'. The bot will ban the subreddit now"
                                          " from the module to escape it automatically.".format(name))
                    except NotFound:
                        pass
                    except Exception as e:
                        import traceback
                        self.logger.error(traceback.print_exc())
                        self.logger.error("{} error: {}".format(responder.BOT_NAME, e))
                self.lock.release()

    def comment_thread(self):
        self.logger.info("Opened comment stream successfully.")
        for comment in self.comments:
            for responder in self.responders:
                self.lock.acquire(True)
                # Check beforehand if a subreddit or a user is banned from the bot / globally.
                if self.database.check_if_subreddit_is_banned(comment.subreddit._case_name, responder.BOT_NAME) and \
                    self.database.check_if_user_is_banned(comment.author.name, responder.BOT_NAME): continue

                if not self.database.get_thing_from_storage(comment.name, responder.BOT_NAME):
                    try:
                        if responder.execute_comment(comment):
                            self.database.insert_into_storage(comment.name, responder.BOT_NAME)

                    except Forbidden:
                        name = comment.subreddit.display_name
                        self.database.add_subreddit_ban_per_module(name,
                                                                   responder.BOT_NAME)
                        self.logger.error("It seems like this bot is banned in '{}'. The bot will ban the subreddit now"
                                          " from the module to escape it automatically.".format(name))
                    except NotFound:
                        pass
                    except Exception as e:
                        import traceback
                        self.logger.error(traceback.print_exc())
                        self.logger.error("{} error: {}".format(responder.BOT_NAME, e))
                self.lock.release()

    def update_thread(self):
        while True:
            self.lock.acquire(True)
            for responder in self.responders:
                threads = self.database.get_all_to_update(responder.BOT_NAME)
                if threads:
                    for thread in threads:
                        # reformat the entry from the database, so we can feed it directly into the update_procedure
                        thread_dict = {'thing_id': thread[0],
                                       'created': strptime(thread[2], '%Y-%m-%d %H:%M:%S'),
                                       'lifetime': strptime(thread[3], '%Y-%m-%d %H:%M:%S'),
                                       'last_updated': strptime(thread[4], '%Y-%m-%d %H:%M:%S'),
                                       'interval': thread[5]}
                        self.database.update_timestamp_in_update(thread_dict['thing_id'], responder.BOT_NAME)
                        try:
                            responder.update_procedure(**thread_dict)
                        except Exception as e:
                            self.logger.error("{} error: {}".format(responder.BOT_NAME, e, e.__traceback__))

            self.database.clean_up_database(int(time()) - int(self.delete_after))
            self.lock.release()

            # after working through all update threads, sleep for five minutes. #saveresources
            sleep(360)

    def submission_stream(self):
        """Opens a new thread, which reads submissions from a specified subreddit."""
        self.submissions = praw.helpers.submission_stream(self.submission_poller, 'all', limit=None, verbosity=0)

    def comment_stream(self):
        """Opens a new thread, which reads comments from a specified subreddit."""
        self.comments = praw.helpers.comment_stream(self.comment_poller, 'all', limit=None, verbosity=0)

    def read_config(self):
        """Reads the config."""
        self.config = ConfigParser()
        self.config.read(path.dirname(__file__) + "/config/config.ini")
        self.logger.info("Configuration read and set up properly.")


if __name__ == "__main__":
    mb = MassdropBot()
