Bot Configuration
=================

There are two different config patterns. One is for the general framework and the other based per plugin.

Framework Config
----------------
The framework currently features no real configuration options. They're hinted at and planned inside
``config/config.ini``, but they have to be implemented first.

Plugin Config
-------------

Every plugin needs to have a base set of configuration (if you use the standard config options), which have to be
present in a particular way:

.. code-block:: py

    [EXAMPLE]
    description = Here could be your description.
    is_logged_in = True
    self_ignore = True
    username = YourUsername
    oauth_file = YourBot_OAuth.ini

If your bot is not logged in, you can ignore the values ``self_ignore``, ``username`` and ``oauth_file``.

Other than that you can use any variable in this section as you please, i. e. storing response strings. The normally
supplied attribute ``config`` in every plugin can be used to load those variables.

















