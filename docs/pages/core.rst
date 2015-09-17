:mod:`Core`: Code Overview
==========================

This documents the all important aspects of the framework. Some objects are hidden, for example
``_SingleLoggingFilter``, since they're part of the base logging system.

:mod:`PluginBase` Group
-----------------------

    The BaseClass is a vital class for the framework. It ensures a given set of features while staying as flexible as
    possible. It also gives an extended feature set which helps with basic tasks necessary with every bot, i. e. logging
    in a bot into reddit, providing the standard config or testing against single, manually input threads and comments.

.. warning:: Do not change the method signature of abstract methods. This will result in a mismatch of a cached abstract
             class meta, resulting in a ``TypeError``. That is an unintended side effect of using abstract base classes.
             When your plugin overwrites the abstract methods, keep the method arguments exactly the same.

             More information: The first found plugin which overwrites the abstract method defines the signature of all
             other plugins. Deep introspections leads you to Base._abc_registry, which is not documented.

.. automodule:: core.baseclass
    :members:
    :private-members:
    :undoc-members:
    :exclude-members: _abc_cache, _abc_negative_cache, _abc_negative_cache_version, _abc_registry

:mod:`RedditRover` Group
------------------------

.. automodule:: core.redditrover
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`Database` Group
---------------------

    This is currently heavily work in progress.

.. automodule:: core.database
    :members:
    :private-members:
    :undoc-members:
    :show-inheritance:

:mod:`LogProvider` Group
------------------------

.. automodule:: core.logprovider
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`MultiThreader` Group
--------------------------

.. automodule:: core.multithreader
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`Handlers` Group
---------------------

.. warning:: PRAW features two more handlers that are not currently covered by this bot. Their architecture is entirely
             different, but RedditRovers' new Handler is faster than the old one.

.. automodule:: core.handlers
    :members:
    :undoc-members:
    :show-inheritance:
