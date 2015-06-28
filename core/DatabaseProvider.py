import logging
import sqlite3
from pkg_resources import resource_filename

# only needed for testing
from time import time


class DatabaseProvider():
    logger = None   # Logger
    db = None       # Reference to DB session
    cur = None      # Reference to DB cursor

    def __init__(self):
        self.logger = logging.getLogger("database")
        self.db = sqlite3.connect(
            resource_filename("core.config", "storage.db"),
            check_same_thread=False,
            isolation_level=None
        )
        self.cur = self.db.cursor()
        self.database_init()

    def __del__(self):
        self.db.close()
        self.logger.warning("DB connection has been closed.")

    def database_init(self):
        if not self.database_check_if_exists('storage'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS storage (thing_id STR(10), bot_module STR(50), timestamp datetime)'
            )
            self.logger.info("Table 'storage' had to be generated.")

        if not self.database_check_if_exists('update_threads'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS update_threads '
                '(thing_id STR(10) NOT NULL, bot_module INT(5), created DATETIME, '
                'lifetime DATETIME, last_updated DATETIME, interval INT(5))'
            )

        if not self.database_check_if_exists('modules'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS modules '
                '(module_name STR(50))'
            )

    def database_check_if_exists(self, table_name):
        self.cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=(?)', (table_name,))
        return self.cur.fetchone()

    def insert_into_storage(self, thing_id, module):
        self.cur.execute('INSERT INTO storage VALUES ((?), (SELECT _ROWID_ FROM modules WHERE module_name=(?)), '
                         'CURRENT_TIMESTAMP)', (thing_id, module))

    def get_all_storage(self):
        self.cur.execute("""SELECT thing_id, module_name, timestamp FROM storage
                            INNER JOIN modules
                            ON storage.bot_module = modules._ROWID_""")
        return self.cur.fetchall()

    def delete_from_storage(self, min_timestamp):
        self.cur.execute("DELETE FROM storage WHERE timestamp <= datetime((?), 'unixepoch')", (min_timestamp,))

    def select_from_storage(self, older_than_timestamp):
        """:param older_than_timestamp: Select all elements in the storage that are older than this timestamp."""
        self.cur.execute("SELECT * FROM storage WHERE timestamp <= datetime((?), 'unixepoch')", (older_than_timestamp,))
        return self.cur.fetchall()

    def insert_into_update(self, thing_id, module, lifetime, interval):
        lifetime = "+{} seconds".format(lifetime)
        self.cur.execute("""
                        INSERT INTO update_threads (thing_id, bot_module, created, lifetime, last_updated, interval)
                            VALUES (
                                (?),
                                (SELECT _ROWID_ FROM modules WHERE module_name=(?)),
                                CURRENT_TIMESTAMP,
                                datetime('now', (?)),
                                CURRENT_TIMESTAMP,
                                (?))
                         """,
                         (thing_id, module, lifetime, interval,))

    def get_all_update(self):
        self.cur.execute("""SELECT thing_id, module_name, created, lifetime, last_updated, interval
                            FROM update_threads
                            INNER JOIN modules
                            ON update_threads.bot_module = modules._ROWID_""")
        return self.cur.fetchall()

    def __select_to_update(self, module):
        self.cur.execute("""SELECT thing_id, module_name, created, lifetime, last_updated, interval
                            FROM update_threads
                            INNER JOIN modules
                            ON update_threads.bot_module = modules._ROWID_
                            WHERE modules.module_name = (?)
                            AND CURRENT_TIMESTAMP > (datetime(update_threads.last_updated,
                                                                '+' || update_threads.interval || ' seconds'))""",
                         (module,))

    def get_latest_to_update(self, module):
        self.__select_to_update(module)
        return self.cur.fetchone()

    def get_all_to_update(self, module):
        self.__select_to_update(module)
        self.cur.fetchall()

    def update_timestamp_in_update(self, thing_id, module):
        self.cur.execute("""UPDATE update_threads
                            SET last_updated=CURRENT_TIMESTAMP
                            WHERE thing_id=(?)
                            AND bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = (?))""",
                         (thing_id, module))

    def delete_from_update(self, thing_id, module):
        self.cur.execute("""DELETE FROM update_threads
                            WHERE thing_id=(?)
                            AND bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = (?))
                            AND CURRENT_TIMESTAMP > lifetime""", (thing_id, module))

    def register_module(self, name):
        self.cur.execute('SELECT COUNT(*) FROM modules WHERE module_name = (?)', (name,))
        if self.cur.fetchone()[0] != 0:
            self.logger.error("Module is already registered.")
            return
        self.logger.debug("Module {} has been registered.".format(name))
        self.cur.execute('INSERT INTO modules VALUES ((?))', (name,))

    def get_all_modules(self):
        self.cur.execute('SELECT _ROWID_, module_name FROM modules')
        return self.cur.fetchall()

    def clean_up_database(self, older_than_unixtime):
        self.cur.execute("""DELETE FROM storage WHERE timestamp < datetime((?), 'unixepoch')""", (older_than_unixtime,))
        self.cur.execute("""DELETE FROM update_threads WHERE CURRENT_TIMESTAMP > lifetime""")

    def wipe_module(self, module):
        self.cur.execute("""DELETE FROM storage
                            WHERE bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = (?))""", (module,))
        self.cur.execute("""DELETE FROM update_threads
                            WHERE bot_module = (SELECT _ROWID_ FROM modules WHERE module_name = (?))""", (module,))
        self.cur.execute("""DELETE FROM modules WHERE module_name = (?)""", (module,))


if __name__ == "__main__":
    db = DatabaseProvider()
    thing_id = "t2_c384fd"
    module = "MassdropBot"
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
#   >> Commands in progress
    print(db.get_all_update())
    print(db.get_all_storage())
    print(db.get_all_modules())