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
                'CREATE TABLE IF NOT EXISTS update_threads (thing_id STR(10), '
                'bot_module STR(50), last_updated datetime, created datetime)'
            )

    def database_check_if_exists(self, table_name):
        self.cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=(?)', (table_name,))
        return self.cur.fetchone()

    def insert_into_storage(self, thing_id, module):
        self.cur.execute('INSERT INTO storage VALUES ((?), (?), CURRENT_TIMESTAMP)', (thing_id, module))

    def insert_into_update(self, thing_id, module):
        self.cur.execute('INSERT INTO update '
                         'VALUES ((?), (?), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)', (thing_id, module))

    def update_in_update(self, thing_id):
        self.cur.execute('UPDATE update WHERE thing_id=(?) VALUES last_updated=CURRENT_TIMESTAMP', (thing_id,))

    def get_latest_to_update(self, module, time_in_hours=1):
        time = time_in_hours*60*60
        self.cur.execute('SELECT * FROM update_threads WHERE module=(?) '
                         'AND WHERE last_updated<(CURRENT_TIMESTAMP - (?))', (module, time))
        return self.cur.fetchone()

    def get_all_to_update(self, module, time_in_hours):
        time = time_in_hours*60*60
        self.cur.execute('SELECT * FROM update_threads WHERE module=(?) '
                         'AND WHERE last_updated<(CURRENT_TIMESTAMP - (?))', (module, time))
        self.cur.fetchall()

    def delete_from_update(self, thing_id):
        self.cur.execute('DELETE FROM update_threads WHERE thing_id=(?)', (thing_id,))

    def clean_up_database(self, unixtime):
        """@TODO: Pls give me better time options."""
        self.cur.execute('DELETE FROM storage WHERE created=(?)', (unixtime,))
        self.cur.execute('DELETE FROM')