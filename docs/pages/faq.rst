FAQ: Common problems and answers
================================

This page discusses about the feature set and the assumptions made by this framework, as well as common problems and
fixes.

What does RedditRover offer?
----------------------------

RedditRover is an easy plugin based bot framework for reddit, reading the most recent submissions and comments.
It features a rich set of features to keep the bot completely automatic, self aware and consistent between sessions.
The framework is documented, easily extensible and features no magic tricks. You can interface with the database however
you please and let the framework revisit generated comments and submissions to update them later. It is certainly faster
as PRAW, due to the Handler limitations fixed within this bot.

What are use cases of RedditRover?
----------------------------------

Everything you would want to do with fresh comments and submissions. Fixing links, remind people, react on messages or
name calling, cross referencing, scrape data, analyzing users - even generating live statistics is easily feasible.
You're not limited within a plugin what you do or how complicated the execution on your plugin is. The framework just
provides you a lot of data live from Reddit.

What assumptions does this framework make?
------------------------------------------

``403 Forbidden``: If you're trying to submit content and the API responds with 403 Forbidden, the framework assumes that
this account is banned or not approved in that subreddit and will set it on the active ban list, effectively ignoring
all submissions or comments from now on.

``APIException: deleted link``, ``InvalidSubmissions``: Sometimes content gets faster deleted than the bot can react to
it (usually a 2-3 second margin) and it is impossible to post on those submissions, the bot will throw a warning and
skip it.

``HTTPException``: Reddits API is accessed a lot and is known to have regular issues. If the bot encounters one of those
it will either retry or simply send a warning and skip the submission. The framework catches HTTPExceptions and retries
the execution on its own and you can annotate your functions with the ``retry``-decorator and catch specific exceptions,
to literally retry after a few seconds.

How does a plugin work?
-----------------------

The most important details are discussed on the `'Writing a Plugin' <pages/writing_a_plugin>_` page. Again, it is
important to inherit from the PluginBase in order to function properly. ``ExampleBot.py`` gives a good insight.

Requests, API limitations, slow framework
-----------------------------------------

Reddit has strict API limits:

- **Not logged in / Auth-cookie sessions:** 30 requests per minute per IP
- **OAuthed sessions**: 60 requests per minute per session

There is a customized RoverHandler to take care exactly of these limitations. However, since PRAW is based on lazy
loading you want to take care of how many requests a plugin produces. In a regular case RedditRover caches a thousand
individual comments and submission. If your plugin triggers on every submission and comment, you will slow down the
framework so intensively, that you won't be able to react on every instance. All working threads get a sleep until it
can dispatch, send and receive a request. To see a detailed log of requests, there is a logfile within
``/logs/[year]/[month]``. If you see a lot oauth-requests you can assume that you have a problem with lazy loading.

My plugin missed a post
-----------------------

There is a slight blindness, especially when Reddit is very busy and/or their API has issues. Also some subreddits do
get hidden from /r/all. As of recent, this isn't only a subreddit setting as some communities (/r/4chan for example)
get automatically removed from /r/all. Monitoring a specific subreddit or a multireddit is however possible. As soon
as the framework doesn't monitor all subreddits anymore, the blindness reduces to near zero. Current tests have shown
that the current miss chance under normal conditions is under 0.005%. This is a problem with Reddit not PRAW or the
framework.

Do you accept donations?
------------------------

Nope. This is a training in software architecture and engineering for me and also a contribution to early programmers
who would like to see how you'd scrape big data from big communities. However, I'd love to add your contribution to the
project.