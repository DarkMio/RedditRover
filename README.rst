.. _main_page:

Reddit Rover
============

.. begin_description

RedditRover is a bot modular bot framework that makes it easy to host all kinds of reddit bots at once.
It is intended to make it easy for new and experienced Programmers to host a variety of bots that can react to Reddits
content without having to mangle with all ins and outs of reddit, praw and API limitations. Running it is easy:

.. code-block:: bash

    $ RedditRover/main.py

That will already do start the entire hosting and loading process - given you have already written a plugin,
it will start shortly after to fire content to your plugin. If there are no plugins so far, the bot will exit
automatically.

.. end_description

.. begin_installation

Installation & Usage
--------------------

Running on Python 3+:

.. code-block:: python

    pip install praw --upgrade

All other dependencies are standard builtins.

.. end_installation

Documentation
-------------
I've tried to document this bot as best as possible. The full documentation can be found here:
`Documentation on Read The Docs <http://redditrover.readthedocs.org/>`_


Debugging
---------
Bot features are written in Abstract ``PluginBase Classes``. Inherit from it and execute one of the test functions:
``test_single_submission(submission_id)``, ``test_single_comment(comment_id)`` or ``_test_single_thing(thing_id)``.
Other than that, use atomic tests of your features however you please. Instantiating a plugin on its own works and
supposed to test your features. Read into the documentation to get a detailed guide how this bot works and what you bot has to do.

Version & Changelog
-------------------
This bot is now again under development. Way less complex code, more segmentation and more single responsibility principle.

.. code-block:: html

    v0.8: Custom handler, providing huge speedups, retry decorators, refactoring, close to initial release
    --------------------------------------------------------------------------------------------------------------
    v0.7: No more praw-OAuth2Util, strengthening the framework, resolving major issues
    v0.6: Recode of the bot. A trillion of new features, which I will document soon
    v0.5: Added more bots - and then it kept fucking up.
    v0.4: Should now load infinite amounts of links, represent them with the website title and respond accordingly.
    v0.3: Fixing behaviour with non-escaped chars in links and stopping the self-spam.
    v0.2: Methods to query with referrer-link and stuff like that
    v0.1: Initial Commit


.. begin_future

Planned features & work in progress
-----------------------------------

- Statistics module, rendering live stats of the bot (should have changeable paths)
- Some interface to control the bot. Mainly restarting, muting, ignoring, etc. Maybe web backend?

.. end_future

.. begin_faq

Help, questions, contribution
-----------------------------

Check out the `FAQ <https://github.com/DarkMio/Massdrop-Reddit-Bot/wiki/FAQ>`_, which should cover most issues.
Pull Requests, emails and messages on Reddit are welcome.

.. end_faq

Thanks for your interest and have a good time.
