# coding=utf-8
import logging
import sqlite3
from pkg_resources import resource_filename


class Database:
    """
    This object provides a full set of features to interface with a basic session database,
       which includes following tables:

       - **storage**:         saves the state of the bot and helps against double posting
       - **update_threads**:  storage to store thing_ids which have to be updated by your plugin
       - **modules**:         persistent module storage
       - **userbans**:        a table to ban users from being able to trigger certain plugins
       - **subbans**:         a table to ban subreddits from being able to trigger certain plugins

    :ivar logger: A database specific database logger. Is currently missing debug-messages for database actions.
    :type logger: logging.Logger
    :vartype logger: logging.Logger
    :ivar db: A connection to the SQLite database: ``/config/storage.db``
    :type db: sqlite3.Connection
    :vartype db: sqlite3.Connection
    :ivar cur: Cursor to interface with the database.
    :type cur: sqlite3.Cursor
    :vartype cur: sqlite3.Cursor
    """

    def __init__(self):
        self.logger = logging.getLogger("database")
        self.db = sqlite3.connect(
            resource_filename("config", "storage.db"),
            check_same_thread=False,
            isolation_level=None
        )
        self.cur = self.db.cursor()
        self.database_init()

    def __del__(self):
        self.db.close()
        self.logger.warning("DB connection has been closed.")

    def database_init(self):
        """
        Initialized the database, checks manually (because: why not?) if those tables already exist and if not, creates
        the necessary tables. You can modify the PRAGMA or add tables however you please, as long as you keep the order
        of these tables (their columns) intact. Some SQL statements are not completely explicit to be independent on
        order.
        """
        info = lambda x: self.logger.info("Table '{}' had to be generated.".format(x))

        if not self._database_check_if_exists('storage'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS storage (thing_id STR(15), bot_module INT(5), timestamp datetime)'
            )
            info('storage')

        if not self._database_check_if_exists('update_threads'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS update_threads '
                '(thing_id STR(15) NOT NULL, bot_module INT(5), created DATETIME, '
                'lifetime DATETIME, last_updated DATETIME, interval INT(5))'
            )
            info('update_threads')

        if not self._database_check_if_exists('modules'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS modules '
                '(module_name STR(50))'
            )
            info('modules')

        if not self._database_check_if_exists('userbans'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS userbans (username STR(50) NOT NULL, bot_module INT(5))'
            )
            info('userbans')

        if not self._database_check_if_exists('subbans'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS subbans (subreddit STR(50) NOT NULL, bot_module INT(5))'
            )
            info('subbans')

    def _database_check_if_exists(self, table_name):
        """
        Helper method to check if a certain table (by name) exists. Refrain from using it if you're not adding new
        tables.
        :param table_name: Name of the table you want to check if it exists.
        :type table_name: str
        :return: Tuple of the table name, empty if it doesn't exist.
        """
        self.cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=(?)', (table_name,))
        return self.cur.fetchone()

    def insert_into_storage(self, thing_id, module):
        """
        Stores a certain thing (id of comment or submission) into the storage, which is for the session consistency.

        :param thing_id: Unique thing_id from a comment or submission.
        :type thing_id: str
        :param module: A string naming your plugin.
        :type module: str
        """
        self.cur.execute('INSERT INTO storage VALUES ((?), (SELECT _ROWID_ FROM modules WHERE module_name=(?)), '
                         'CURRENT_TIMESTAMP)', (thing_id, module))
        self.logger.debug('{} from {} inserted into storage.'.format(thing_id, module))

    def get_all_storage(self):
        """
        Returns all elements inside the bot storage.

        :return: Tuple with tuples with all storage elements with ``(thing_id, module_name, timestamp)``
        """
        self.cur.execute("""SELECT thing_id, module_name, timestamp FROM storage
                            INNER JOIN modules
                            ON storage.bot_module = modules._ROWID_""")
        return self.cur.fetchall()

    def retrieve_thing(self, thing_id, module):
        """
        Returns a single thing from the storage by thing_id and module name. Mainly used to check if a plugin already
        answered on a post.

        :param thing_id: Unique thing_id from a comment or submission.
        :type thing_id: str
        :param module: A string naming your plugin.
        :type module: str
        :return: Tuple with ``(thing_id, bot_module, timestamp)``
        """
        self._error_if_not_exists(module)
        self.cur.execute("""SELECT thing_id, bot_module, timestamp FROM storage
                            WHERE thing_id = (?)
                            AND bot_module = (SELECT _ROWID_ FROM modules WHERE module_name=(?))
                            LIMIT 1""",
                         (thing_id, module,))
        return self.cur.fetchone()

    def delete_from_storage(self, min_timestamp):
        """
        Deletes **all** items which are older than the given timestamp.

        :param min_timestamp: Unix timestamp where all entries in storage get deleted if they're older than that.
        :type min_timestamp: int | float
        """
        self.cur.execute("DELETE FROM storage WHERE timestamp <= datetime((?), 'unixepoch')", (min_timestamp,))
        self.logger.debug('Deleted everything from storage older than {}'.format(min_timestamp))

    def select_from_storage(self, older_than_timestamp):
        """
        Selects and retrieves all elements in the storage which are older than this timestamp.

        :param older_than_timestamp: Unix timestamp of which time everything has to be selected before.
        :type older_than_timestamp: int | float
        :return: Tuples of ``(thing_id, bot_module, timestamp)``
        """
        self.cur.execute("SELECT * FROM storage WHERE timestamp <= datetime((?), 'unixepoch')", (older_than_timestamp,))
        return self.cur.fetchall()

    def insert_into_update(self, thing_id, module, lifetime, interval):
        """
        Inserts a thing_id (from a comment or submission) into the update-table, which later gets retrieved from the
        update-thread and fired onto the plugin.

        :param thing_id: Unique thing_id from a comment or submission.
        :type thing_id: str
        :param module: A string naming your plugin.
        :type module: str
        :param lifetime: Lifetime until this item is valid in Unix timestamp.
        :type lifetime: float | int
        :param interval: Interval of how often you'd want this to update in seconds.
        :type interval: int
        """
        self._error_if_not_exists(module)
        self.cur.execute("""
                        INSERT INTO update_threads (thing_id, bot_module, created, lifetime, last_updated, interval)
                            VALUES (
                                (?),
                                (SELECT _ROWID_ FROM modules WHERE module_name=(?)),
                                CURRENT_TIMESTAMP,
                                datetime('now', '+' || (?) || ' seconds'),
                                CURRENT_TIMESTAMP,
                                (?))
                         """,
                         (thing_id, module, lifetime, interval,))
        self.logger.debug('Inserted {} from {} to update - lifetime: {} | interval: {}'.format(thing_id, module,
                                                                                               lifetime, interval))

    def get_all_update(self):
        """
        Returns all elements inside the update_htreads table.

        :return: Tuple with tuples of ``(thing_id, module_name, created, lifetime, last_updated, interval)``
        """
        self.cur.execute("""SELECT thing_id, module_name, created, lifetime, last_updated, interval
                            FROM update_threads
                            INNER JOIN modules
                            ON update_threads.bot_module = modules._ROWID_
                            ORDER BY last_updated ASC""")
        return self.cur.fetchall()

    def _select_to_update(self, module):
        """
        Selector method to get the cursor selecting all outstanding threads to update for a certain module. Refrain from
        using it, since it only places the cursor.

        :param module: A string naming your plugin.
        :type module: str
        """
        self._error_if_not_exists(module)
        self.cur.execute("""SELECT thing_id, module_name, created, lifetime, last_updated, interval
                            FROM update_threads
                            INNER JOIN modules
                            ON update_threads.bot_module = modules._ROWID_
                            WHERE modules.module_name = (?)
                            AND CURRENT_TIMESTAMP > (datetime(update_threads.last_updated,
                                                                '+' || update_threads.interval || ' seconds'))
                            ORDER BY last_updated ASC""",
                         (module,))

    def get_latest_to_update(self, module):
        """
        Returns a single thing_id (from comment or submssion) for a single module.

        :param module: A string naming your plugin.
        :type module: str
        :return: Tuple with tuples of ``(thing_id, module_name, created, lifetime, last_updated, interval)``
        """
        self._select_to_update(module)
        return self.cur.fetchone()

    def get_all_to_update(self, module):
        """
        Returns **all** thing_ids (from a comment or submission) for a module.

        :param module: A string naming your plugin.
        :type module: str
        :return: Tuple with tuples of ``(thing_id, module_name, created, lifetime, last_updated, interval)``
        """
        self._select_to_update(module)
        return self.cur.fetchall()

    def update_timestamp_in_update(self, thing_id, module):
        """
        Updates the timestamp when a thing_id was updated last.

        :param thing_id: Unique thing_id from a comment or submission.
        :type thing_id: str
        :param module: A string naming your plugin.
        :type module: str
        """
        self._error_if_not_exists(module)
        self.cur.execute("""UPDATE update_threads
                            SET last_updated=CURRENT_TIMESTAMP
                            WHERE thing_id=(?)
                            AND bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = (?))""",
                         (thing_id, module))
        self.logger.debug('Updated timestamp on {} from {}'.format(thing_id, module))

    def delete_from_update(self, thing_id, module):
        """
        Deletes **all** thing_ids (from a comment or submission) for a module when it outlived its lifetime.

        :param thing_id: Unique thing_id from a comment or submission.
        :type thing_id: str
        :param module: A string naming your plugin.
        :type module: str
        """
        self._error_if_not_exists(module)
        self.cur.execute("""DELETE FROM update_threads
                            WHERE thing_id=(?)
                            AND bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = (?))
                            AND CURRENT_TIMESTAMP > lifetime""", (thing_id, module))

    def register_module(self, module):
        """
        Registers a module if it hasn't been so far. A module has to be registered to be useable with the rest of the
        database.
        :param module: A string naming your plugin.
        :type module: str
        """
        if self._check_if_module_exists(module):
            return
        self.cur.execute('INSERT INTO modules VALUES ((?))', (module,))
        self.logger.debug("Module {} has been registered.".format(module))

    def get_all_userbans(self):
        """
        Returns all bans stored in the userban table.
        :return: Tuple of tuples ``(username, bot_module)``
        """
        self.cur.execute('SELECT * FROM userbans')
        return self.cur.fetchall()

    def get_all_bans_per_user(self, username):
        """
        Returns all bans of a particular user across all plugins.
        :param username: Author in fulltext in question
        :type username: str
        :return: Tuple of tuples ``(username, bot_module)``
        """
        self.cur.execute('SELECT * FROM userbans WHERE username = (?) LIMIT 1', (username,))
        return self.cur.fetchall()

    def check_user_ban(self, username, module):
        """
        Checks if a particular user has been banned, first searches per module, then if there is a global ban.

        :param username: Author in fulltext in question
        :type username: str
        :param module: A string naming your plugin.
        :type module: str
        :return: Boolean if banned or not.
        """
        self.cur.execute('SELECT * FROM userbans '
                         'WHERE username = (?) AND '
                         'bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = (?)) '
                         'LIMIT 1', (username, module))
        if self.cur.fetchone():
            return True

        self.cur.execute('SELECT * FROM userbans '
                         'WHERE username = (?) AND '
                         'bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = NULL    ) '
                         'LIMIT 1', (username,))
        return self.cur.fetchone() is True

    def add_userban_per_module(self, username, module):
        """
        Bans a user for a certain module.

        :param username: Author in fulltext in question
        :type username: str
        :param module: A string naming your plugin.
        :type module: str
        """
        self.cur.execute("INSERT INTO userbans (username, bot_module) "
                         "VALUES ((?), (SELECT _ROWID_ FROM modules WHERE module_name = (?)))", (username, module))
        self.logger.debug('User {} got banned on {}'.format(username, module))

    def add_userban_globally(self, username):
        """
        Bans a user for all modules.

        :param username: Author in fulltext in question
        :type username: str
        """
        self.cur.execute("INSERT INTO userbans (username, bot_module) "
                         "VALUES ((?), NULL)", (username,))
        self.logger.debug('User {} got banned across all modules.'.format(username))

    def remove_userban_per_module(self, username, module):
        """
        Removes a ban from a certain modules.

        :param username: Author in fulltext in question
        :type username: str
        :param module: A string naming your plugin.
        :type module: str
        """
        self.cur.execute("DELETE FROM userbans WHERE username = (?) AND "
                         "bot_module = (SELECT _ROWID_ FROM modules WHERE modules = (?))", (username, module))
        self.logger.debug('User {} got unbanned on {}'.format(username, module))

    def remove_userban_globally(self, username):
        """
        Removes **all** bans for a user. Globally and per module level.

        :param username: Author in fulltext in question
        :type username: str
        """
        self.cur.execute("DELETE FROM userbans WHERE username = (?)", (username,))
        self.logger.debug('User {} got unbanned across all modules.'.format(username))

    def purge_all_user_bans(self):
        """
        Removes **all** bans for **all** users - no exception, clears the entire table.
        """
        self.cur.execute("DELETE FROM userbans")
        self.logger.debug('Removed all userbans!')

    def get_all_banned_subreddits(self):
        """
        Returns all bans stored in the subreddit ban table
        """
        self.cur.execute('SELECT * FROM subbans')
        return self.cur.fetchall()

    def get_all_bans_per_subreddit(self, subreddit):
        """
        Returns **all** bans for a particular subreddit
        :param subreddit: Author in fulltext in question
        :type subreddit: str
        """
        self.cur.execute('SELECT * FROM subbans WHERE subreddit = (?) LIMIT 1', (subreddit,))
        return self.cur.fetchall()

    def check_subreddit_ban(self, subreddit, module):
        """
        Returns if a certain subreddit is banned from a module or across all modules.

        :param subreddit: Author in fulltext in question
        :type subreddit: str
        :param module: A string naming your plugin.
        :type module: str
        :return: Boolean, True if banned, False if not.
        """
        self.cur.execute('SELECT * FROM subbans '
                         'WHERE subreddit = (?) AND '
                         'bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = (?)) '
                         'LIMIT 1', (subreddit, module))
        if self.cur.fetchone():
            return True

        self.cur.execute('SELECT * FROM subbans '
                         'WHERE subreddit = (?) AND '
                         'bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = NULL    ) '
                         'LIMIT 1', (subreddit,))
        return self.cur.fetchone() is True

    def add_subreddit_ban_per_module(self, subreddit, module):
        """
        Bans a subreddit from a certain module.

        :param subreddit: Author in fulltext in question
        :type subreddit: str
        :param module: A string naming your plugin.
        :type module: str
        """
        self.cur.execute("INSERT INTO subbans (subreddit, bot_module) "
                         "VALUES ((?), (SELECT _ROWID_ FROM modules WHERE module_name = (?)))", (subreddit, module))
        self.logger.debug('Subreddit {} got banned on {}'.format(subreddit, module))

    def add_subreddit_ban_globally(self, subreddit):
        """
        Bans a subreddit across all subreddits.

        :param subreddit: Author in fulltext in question
        :type subreddit: str
        """
        self.cur.execute("INSERT INTO subbans (subreddit, bot_module) "
                         "VALUES ((?), NULL)", (subreddit,))
        self.logger.debug('Subreddit {} got banned across all modules.'.format(subreddit))

    def remove_subreddit_ban_per_module(self, subreddit, module):
        """
        Removes a subreddit ban for a certain module

        :param subreddit: Author in fulltext in question
        :type subreddit: str
        :param module: A string naming your plugin.
        :type module: str
        """
        self.cur.execute("DELETE FROM subbans WHERE subreddit = (?) AND "
                         "bot_module = (SELECT _ROWID_ FROM modules WHERE modules = (?))", (subreddit, module))
        self.logger.debug('Subreddit {} got unbanned on {}'.format(subreddit, module))

    def remove_subreddit_ban_globally(self, subreddit):
        """
        Removes a subreddit ban across all modules and globally

        :param subreddit: Author in fulltext in question
        :type subreddit: str
        """
        self.cur.execute("DELETE FROM subbans WHERE subreddit = (?)", (subreddit,))
        self.logger.debug('Subreddit {} got unbanned across all modules.'.format(subreddit))

    def purge_all_subreddit_bans(self):
        """
        Removes all subreddit bans from the table - no exceptions, clears the table.
        """
        self.cur.execute("DELETE FROM subbans")
        self.logger.debug('All subreddit bans removed!')

    def _check_if_module_exists(self, module):
        """
        Helper method to determine if a module has already been registered. Refrain from using it, hence it is private.

        :param module: A string naming your plugin.
        :type module: str
        :return: Boolean determining if a module already has been registered.
        :raise ValueError: In case of a module being registered multiple times - which should never happen - the
                           ``Database`` object will raise a value error.
        """
        self.cur.execute('SELECT COUNT(*) FROM modules WHERE module_name = (?)', (module,))
        result = self.cur.fetchone()
        if result[0] == 0:
            return False
        if result[0] == 1:
            return True
        if result[0] > 1:
            raise ValueError("A module was registered multiple times and is therefore inconsistent. Call for help.")

    def _error_if_not_exists(self, module):
        """
        Helper method for throwing a concrete error if a module has not been registered, yet tries to write into the
        database without having a reference.

        :param module: A string naming your plugin.
        :type module: str
        :raise LookupError: If the module doesn't exist, it raises an error.
        """
        if not self._check_if_module_exists(module):
            raise LookupError('The module where this operation comes from is not registered!')

    def get_all_modules(self):
        """
        Returns all modules that have been registered so far.

        :return: Tuple of tuples ``(_ROWID_, module_name)``
        """
        self.cur.execute('SELECT _ROWID_, module_name FROM modules')
        return self.cur.fetchall()

    def clean_up_database(self, older_than_unixtime):
        """
        Cleans up the database, meaning that everything older than the session time and all threads that should be
        updated and outlived their lifetime will be deleted.

        :param older_than_unixtime: Unix timestamp from which point entries have to be older than to be deleted.
        :type older_than_unixtime: int | float
        """
        self.cur.execute("""DELETE FROM storage WHERE timestamp < datetime((?), 'unixepoch')""", (older_than_unixtime,))
        self.cur.execute("""DELETE FROM update_threads WHERE CURRENT_TIMESTAMP > lifetime""")
        self.logger.debug('Database cleanup: All storage items older than '
                          '{} and all deprecated update-threads removed'.format(older_than_unixtime))

    def wipe_module(self, module):
        """
        Wipes a module across all tables and all its references.

        :param module: A string naming your plugin.
        :type module: str
        """
        self.cur.execute("""DELETE FROM storage
                            WHERE bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = (?))""", (module,))
        self.cur.execute("""DELETE FROM update_threads
                            WHERE bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = (?))""", (module,))
        self.cur.execute("""DELETE FROM modules WHERE module_name = (?)""", (module,))
        self.logger.debug("{} got wiped from all tables and all its references.".format(module))


if __name__ == "__main__":
    pass
#   db = Database()
#   thing_id = "t2_c384fd"
#   module = "MassdropBot"
#   user = "MioMoto"
#   subreddit = "dota2"
#   Commands that work:
#   >> Storage
#   db.insert_into_storage(thing_id, module)
#   print(db.get_all_storage())
#   print(db.select_from_storage(int(time())))
#
#   >> Module Register
#   db.register_module(module)
#   print(db.get_all_modules())
#
#   >> update_threads
#   db.insert_into_update(thing_id, module, 600, 15)
#   print(db.get_latest_to_update('MassdropBot'))
#   print(db.get_all_update())
#   db.update_timestamp_in_update(thing_id, module)
#   db.delete_from_update(thing_id, module)
#
#   >> Cleanup
#   db.clean_up_database(int(time()) - 30)
#   db.wipe_module(module)
#
#   >> Printing out the current state of all tables
#    print(db.get_all_update())
#    print(db.get_all_storage())
#    print(db.get_all_modules())
#
#   >> Subreddit Bans
#   db.purge_all_subreddit_bans()
#   db.add_subreddit_ban_per_module(user, module)
#   db.add_subreddit_ban_globally(user)
#   print(db.check_if_subreddit_is_banned(user, "abc"))
#   print(db.get_all_bans_per_subreddit(user))
#   print(db.get_all_banned_subreddits())
#   db.remove_subreddit_ban_globally(user)
#   print(db.get_all_banned_subreddits())
#
#   >> User Bans
#   db.purge_all_user_bans()
#   db.add_userban_per_module(user, module)
#   db.add_userban_globally(user)
#   print(db.check_if_user_is_banned(user, "abc"))
#   print(db.get_all_bans_per_user(user))
#   print(db.get_all_userbans())
#   db.remove_userban_globally(user)
#   print(db.get_all_userbans())
