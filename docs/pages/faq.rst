FAQ: Common problems and answers
================================

How does a plugin work?
-----------------------

The most important details are discussed on the `'Writing a Plugin' <pages/writing_a_plugin>_` page. Again, it is
important to inherit from the PluginBase in order to function properly. ``ExampleBot.py`` gives a good insight.

Requests, API limitations, slow framework
-----------------------------------------

Reddit has strict API limits:

- **Not logged in / Authcookie sessions:** 30 requests per minute per IP
- **OAuthed sessions**: 60 requests per minute per session