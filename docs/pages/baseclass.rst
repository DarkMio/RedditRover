BaseClass methods
=================

The BaseClass is a vital class for the framework. It ensures a given set of features while staying as flexible as
possible. It also gives an extended feature set which helps with basic tasks necessary with every bot, i. e. logging in
a bot into reddit, providing the standard config or testing against single, manually input threads and comments.

Abstract methods
----------------

Within the Base are a couple of abstract methids, all of which have to be overwritten. The plugin won't be imported if
those core features are not overwritten.

.. py:class:: core.BaseClass.Base(database, bot_name, setup_from_config=True)

.. py:function:: execute_submission(self, submission)

    Class Method which receives a single ``praw.objects.Submission`` object resulting from a self.post on Reddit.
 :param self: Object pointer
    :param submission: A single submission which includes a textbody (self.post)
    :rtype: Bool or NoneType


.. py:function:: execute_link(self, link_submission):

    Class Method which receives a single ``praw.objects.Submission`` object resulting from a link post on Reddit.

    :param self: Object pointer
    :param submission: A single submission which includes an url. (link post)
    :rtype: Bool or NoneType

.. py:function:: execute_titlepost(self, title_only):

    Class Method which receives a single ``praw.objects.Submission`` object, which has neither a text body nor an url.
    It is basically just the title of a submission.

    :param self: Object pointer
    :param submission: A single submission which has neither text nor url.
    :rtype: Bool or NoneType

.. py:function:: execute_comment(self, comment):

    Class Method which receives a single ``praw.objects.Comment`` object from a comment on a thread.

    :param self: Object pointer
    :param submission: A single comment.
    :rtype: Bool or NoneType

.. py:function:: update_procedure(self, thing_id, created, lifetime, last_updated, interval):

    Gets called when you stored a comment or a submission in the update table.

    :param self: Object pointer
    :param thing_id: A single comment.
    :param created: Moment of creation of this entry
    :type created: time.struct_time
    :param lifetime: Moment when entry outlived his update interval
    :type lifetime: time.struct_time
    :param last_updated: Moment when the entry has been updated last
    :type last_updated: time.struct_time
    :param interval: Update interval in seconds
    :type interval: Integer
    :rtype: Bool or NoneType

.. py:function:: on_new_message(self, message):

    Class Method that gets called whenever the bot received a new message.

    :params self: Object pointer
    :param message: A PRAW Message
    :type message: praw.objects.Message


Object methods
--------------

There are two types of builtin methods: Vital framework methods or testing features, i. e. the integrity check, and
methods for easy plugin programming, i. e. methods for storing submissions you want to update or a simple bot banning
feature (to ignore users and subreddits consistently).

.. py:function:: integrity_check(self)

    Checks the integrity of said plugin based on standard parameter. It gets called after object initialization and
    verifies the most important attributes.

.. py:function:: factory_logger(self)

    Adds an attribute ``logger`` to the object, which is standard logging object.

.. py:function:: factory_reddit(self, config_path)

    Adds two attributes ``session`` (reddit session) and ``oauth`` (oauth util) to the object and logs in a plugin.

.. py:function:: factory_config(self)

    Adds an attribute ``config`` to the object, which is a ConfigParser plugin pointing at ``core/bot_config.ini``

.. py:function:: standard_setup(self, bot_name)

    Sets up standard attributes of a plugin based on the assumption that a section with that ``bot_name`` is configured
    in ``core/bot_config.ini``. Those attributes are all used for reddit session, i. e. description, if a plugin is
    logged in, username and OAuth config path.

.. py:function:: standard_ban_procedure(self, message, subreddit_banning_allowed=True, user_banning_allowed=True):

    An exemplary method that bans users and subs and then replies them that the bot has banned.
    Needs a reddit session, oauth and a database pointer to function properly.

    :param message: a single praw message object
    :type message: praw.objects.Message
    :param subreddit_banning_allowed: can block out the banning of subreddits
    :type subreddit_banning_allowed: bool
    :param user_banning_allowed: can block out the banning of users
    :type user_banning_allowed: bool
    :return:

.. py:function:: __test_single_thing(self, thing_id):

        If you're used to reddit thing ids, you can use this method directly.
        However, if that is not the case, use test_single_submission and test_single_comment.

.. py:function:: test_single_submission(self, submission_id):

        Use this method to test you bot manually on submissions.

.. py:function:: test_single_comment(self, comment_id):

        Use this method to test your bot manually on a single comment.

.. py:function:: to_update(self, response_object, lifetime):

    This method is preferred if you want a submission or comment to be updated.

    :param response_object: PRAW returns on a posted submission or comment the resulting object.
    :type response_object: praw.objects.Submission or praw.objects.Comment
    :param lifetime: The exact moment in unixtime utc+0 when this object will be invalid (update cycle)
    :type lifetime: unixtime in seconds


Object Attributes
-----------------

There are certain attributes you could overwrite as you please. Otherwise setting them up with the presented tools is
recommended.

.. py:attribute:: DESCRIPTION

    Reddit user agent: describes the bot / function / author

.. py:attribute:: USERNAME

    reddit username which should be logged in - checked on integrity check if it is the same than what the OAuth
    credentials log in with.

.. py:attribute:: OAUTH_FILENAME

    login credentials path for praw-OAuth2Util

.. py:attribute:: BOT_NAME

    Give the bot a nice name.

.. py:attribute:: IS_LOGGED_IN

    Mandatory bool if this bot features a logged in session

.. py:attribute:: SELF_IGNORE

    Bool if the bot should not react on his own submissions / comments.

.. py:attribute:: session

    a full session with login into reddit.

.. py:attribute:: oauth

    praw-OAuth2Util

.. py:attribute:: logger

    logger for specific module

.. py:attribute:: config

    Could be used for ConfigParser - there is a method for that.

.. py:attribute:: database

    Session to database.
