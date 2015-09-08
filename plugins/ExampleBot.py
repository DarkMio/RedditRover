from core.BaseClass import Base


class ExampleBot(Base):
    def __init__(self, database, handler):
        super().__init__(database, handler, 'MassdropBot')

    def execute_comment(self, comment):
        pass

    def execute_titlepost(self, title_only):
        pass

    def execute_link(self, link_submission):
        pass

    def execute_submission(self, submission):
        pass

    def update_procedure(self, thing_id, created, lifetime, last_updated, interval):
        pass

    def on_new_message(self, message):
        self.standard_ban_procedure(message)
        pass


def init(database, handler):
    """Init Call from module importer to return only the object itself, rather than the module."""
    return ExampleBot(database, handler)
