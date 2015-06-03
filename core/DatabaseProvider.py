import logging
import sqlite3
from pkg_resources import resource_filename


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
                'CREATE TABLE IF NOT EXISTS storage (thing_id STR(10), bot_module STR(50), DateTime datetime)'
            )
            self.logger.info("Table 'storage' had to be generated.")

        if not self.database_check_if_exists('update'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS update_threads '
                '(thing_id STR(10) NOT NULL, bot_module_id INT(5), created DATETIME, '
                'lifetime DATETIME, last_updated DATETIME, interval INT(5))'
            )

        if not self.database_check_if_exists('modules'):
            self.cur.execute(
                'CREATE TABLE IF NOT EXISTS modules '
                '(id INT(5) NOT NULL PRIMARY KEY, module_name STR(50))'
            )

    def database_check_if_exists(self, table_name):
        self.cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=(?)', (table_name,))
        return self.cur.fetchone()

    def insert_into_storage(self, thing_id, module):
        self.cur.execute('INSERT INTO storage VALUES ((?), (?), CURRENT_TIMESTAMP)', (thing_id, module))

    def insert_into_update(self, thing_id, module, lifetime, interval):
        self.cur.execute('INSERT INTO update '
                         'VALUES ((?), (?), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP+(?), CURRENT_TIMESTAMP, (?))',
                         (thing_id, module, lifetime, interval,))

    def update_in_update(self, thing_id):
        self.cur.execute('UPDATE update WHERE thing_id=(?) VALUES last_updated=CURRENT_TIMESTAMP', (thing_id,))

    def get_latest_to_update(self, module):
        self.cur.execute('SELECT * FROM update_threads WHERE module=(?) '
                         'AND WHERE CURRENT_TIMESTAMP > (last_updated+interval) '
                         'MAX 1', (module,))
        return self.cur.fetchone()

    def get_all_to_update(self, module):
        self.cur.execute('SELECT * FROM update_threads WHERE module=(?) '
                         'AND WHERE CURRENT_TIMESTAMP > (last_updated+interval)', (module,))
        self.cur.fetchall()

    def delete_from_update(self, thing_id):
        self.cur.execute('DELETE FROM update_threads WHERE thing_id=(?) '
                         'AND WHERE created < (last_updated - timespan)', (thing_id,))

    def clean_up_database(self, unixtime):
        """@TODO: Pls give me better time options."""
        self.cur.execute('DELETE FROM storage WHERE created=(?)', (unixtime,))
        self.cur.execute('DELETE FROM')

    def register_module(self, name):
        last_id = 0
        self.cur.execute('INSERT INTO modules ((?), (?))', (last_id+1, name))


if __name__ == "__main__":
    db = DatabaseProvider()
    thing_id = "t2_c384fd"
    module = "MassdropBot"
    db.insert_into_storage(thing_id, module)
    db.insert_into_update(thing_id, module, 1000, 20)

    while True:
        print(db.get_latest_to_update(module))
        # from time