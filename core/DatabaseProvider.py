import logging
import sqlite3
from pkg_resources import resource_filename


class DatabaseProvider():
    logger = None       # Logger
    db = None           # Reference to DB session
    cur = None          # Reference to DB cursor

    def __init__(self):
        self.logger = logging.getLogger("database")
        self.db = sqlite3.connect(
                            resource_filename("core.config", "storage.db"),
                            check_same_thread=False,
                            isolation_level=None
                            )
        self.cur = self.db.cursor()
        self.database_init()

    def database_init(self):
        if not self.database_check_if_exists('storage'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS storage (thing_id STR(10), bot_module STR(50), DateTime datetime)'
            )
            self.logger.info("Table 'storage' had to be generated.")

        if not self.database_check_if_exists('update'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS update_threads (thing_id STR(10), bot_module STR(50), DateTime datetime)'
            )

    def database_check_if_exists(self, channel):
        self.cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=(?)', (channel,))
        return self.cur.fetchone()