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
    :type logger: logging.Logger
    :ivar config: Holds a full set of configs from the configfile.
    :vartype config: ConfigParser
    :type config: ConfigParser
    :ivar responders: A list of plugins the bot is running. @TODO: Exit the bot if no plugin is found.
    :vartype responders: list
    :type responders: list
    :ivar multi_thread: The MultiThreader instance, which manages daemonic threads.
    :vartype multi_thread: MultiThreader
    :type multi_thread: MultiThreader
    :ivar delete_after: All activity older than x seconds will be cleaned up from the database.
    :vartype delete_after: int
    :type delete_after: int
    :ivar praw_handler: Will hold the handler to RateLimit based on OAuth / No-Auth sessions.
    :vartype praw_handler: RedditRoverHandler
    :type praw_handler: RedditRoverHandler
    :ivar submission_poller: Anonymous reddit session for submissions.
    :vartype submission_poller: praw.Reddit
    :type submission_poller: praw.Reddit
    :ivar comment_poller: Anonymous reddit session for comments.
    :vartype comment_poller: praw.Reddit
    :type comment_poller: praw.Reddit
    :ivar submissions: Generator of recent submissions on Reddit.
    :vartype submissions: praw.helpers.comment_stream
    :type submissions: praw.helpers.comment_stream
    :ivar comments: Generaot of recent comments on Reddit.
    :vartype comments: praw.helpers.comment_stream
    :type comments: praw.helpers.comment_stream
    """

    def __init__(self):
        warning_filter.ignore()
        self.logger = logprovider.setup_logging(log_level="DEBUG")
        self.config = ConfigParser()
        self.config.read(resource_filename('config', 'bot_config.ini'))
        self.mark_as_read, self.catch_http_exception, self.delete_after, self.verbose = self._bot_variables()
        self.multi_thread = MultiThreader()
        self.lock = self.multi_thread.get_lock()
        self.database_update = Database()
        self.database_cmt = Database()
        self.database_subm = Database()
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
        self.submissions = praw.helpers.submission_stream(self.submission_poller, 'all', limit=None, verbosity=0)
        self.comments = praw.helpers.comment_stream(self.comment_poller, 'all', limit=None, verbosity=0)
        self.multi_thread.go([self.comment_thread], [self.submission_thread], [self.update_thread])
        self.multi_thread.join_threads()

    def _bot_variables(self):
        """
        Gets all relevant variables for this bot from the configuration
        :return:
        """
        get_b = lambda x: self.config.getboolean('RedditRover', x)
        get_i = lambda x: self.config.getint('RedditRover', x)
        return get_b('mark_as_read'), get_b('catch_http_exception'), get_i('delete_after'), get_b('verbose')

    def _filter_single_thing(self, thing, responder):
        """
        Helper method to filter out submissions, returns `True` or `False` depending if it hits or fails.

        :param thing: Single submission or comment
        :type thing: praw.objects.Comment | praw.objects.Submission
        :param responder: Single plugin
        :type responder: PluginBase
        """
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
        """
        Loads all plugins from ./plugins/, appends them to a list of responders and verifies that they're properly setup
        and working for the main bot process.
        """
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
            module_object = module.init(Database(), self.praw_handler)
            try:
                if not isinstance(module_object, PluginBase):
                    raise ImportError('Module {} does not inherit from PluginBase class'.format(
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
        if len(self.responders) == 0:
            self.logger.info('No plugins found and / or working, exiting RedditRover.')
            sys.exit(0)
        self.logger.info("Imported a total of {} object(s).".format(len(self.responders)))

    def submission_thread(self):
        """
        The submission thread runs down all submission from the specified sub (usually /r/all),
        then filters out all banned users and subreddits and then fires submissions at your plugins.
        """
        self.logger.info("Opened submission stream successfully.")
        for subm in self.submissions:
            self.comment_submission_worker(subm)

    def comment_thread(self):
        """
        The comment thread runs down all comments from the specified sub (usually /r/all),
        then filters out banned users and subreddits and fires it at your plugins.
        """
        self.logger.info("Opened comment stream successfully.")
        for comment in self.comments:
            self.comment_submission_worker(comment)

    def comment_submission_worker(self, thing):
        """
        Runs through all available plugins, filters them based on that out and calls the right method within a plugin.

        :param thing: Single submission or comment
        :type thing: praw.objects.Comment | praw.objects.Submission
        """
        for responder in self.responders:
            # Check beforehand if a subreddit or a user is banned from the bot / globally.
            if self._filter_single_thing(thing, responder):
                try:
                    self.comment_submission_action(thing, responder)
                except Exception as e:
                    self.logger.error(traceback.print_exc())
                    self.logger.error("{} error: {} < {}".format(responder.BOT_NAME, e.__class__.__name__, e))

    @retry(HTTPException)  # when the API fails, we're here to catch that.
    def comment_submission_action(self, thing, responder):
        """
        Separated function to run a single submission or comment through a single comment.

        :param thing: single submission or comment
        :type thing: praw.objects.Submission | praw.objects.Comment
        :param responder: single plugin
        :type responder: PluginBase
        :return:
        """
        try:
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
        except Forbidden:
            name = thing.subreddit.display_name
            self.database_subm.add_subreddit_ban_per_module(name, responder.BOT_NAME)
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
        except HTTPException as e:
            if self.catch_http_exception:
                self.logger.error('{} encountered: HTTPException - probably Reddits API.'.format(responder.BOT_NAME))
            else:
                raise e
        except Exception as e:
            raise e

    def update_thread(self):
        """
        The update-thread does a lot of different tasks.
        First it loads all threads that have to update and executes the update_procedure of your plugin.
        Then it loads all unread messages of your plugin, cleans up the database and sleeps for 5 minutes.
        """
        while True:
            self.lock.acquire(True)
            for responder in self.responders:
                threads = self.database_update.get_all_to_update(responder.BOT_NAME)
                try:
                    for thread in threads:
                        self.update_action(thread, responder)
                    responder.get_unread_messages(self.mark_as_read)
                except HTTPException as e:
                    if self.catch_http_exception:
                        self.logger.error('{} encountered: HTTPException - probably Reddits API.'.format(
                            responder.BOT_NAME))
                    else:
                        raise e
                except Exception as e:
                    self.logger.error(traceback.print_exc())
                    self.logger.error("{} error: {} < {}".format(responder.BOT_NAME, e.__class__.__name__, e))
            self.database_update.clean_up_database(int(time()) - int(self.delete_after))
            self.lock.release()
            # after working through all update threads, sleep for five minutes. #saveresources
            sleep(360)  # @TODO: Needs a config option

    @retry(HTTPException)  # when the API bugs out, we retry it for a while, this thread has time for it anyway.
    def update_action(self, thread, responder):
        """
        Separated function to map a thing to update and feed it back into a plugin.

        :param thread: A tuple containing information from the database.
        :type thread: tuple
        :param responder: A single plugin
        :type responder: PluginBase
        """
        # reformat the entry from the database, so we can feed it directly into the update_procedure
        time_strip = lambda x: strptime(x, '%Y-%m-%d %H:%M:%S')
        self.database_update.update_timestamp_in_update(thread[0], responder.BOT_NAME)
        # Accessing the thread_info from the responder _could_ be unsafe, but it's immensely faster.
        responder.update_procedure(thing=responder.session.get_info(thing_id=thread[0]),
                                   created=time_strip(thread[2]),
                                   lifetime=time_strip(thread[3]),
                                   last_updated=time_strip(thread[4]),
                                   interval=thread[5])

if __name__ == "__main__":
    mb = RedditRover()
