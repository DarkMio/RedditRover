from core.BaseClass import Base


class Massdrop(Base):

    def __init__(self):
        super().__init__()
        super().factory_config()
        self.DESCRIPTION = self.config.get('MassdropBot', 'description')
        self.USERNAME = self.config.get('MassdropBot', 'username')
        self.PASSWORD = self.config.get('MassdropBot', 'password')
        self.REGEX = r"^(https?://)?(www.)?(massdrop.com/buy/)(?P<product>.*)(\?.*)"
        self.factory_reddit()

    def execute_comment(self, comment):
        pass

    def execute_submission(self, submission):
        pass

    def update_procedure(self, thing_id):
        pass


def init():
    """Init Call from module importer to return only the object itself, rather than the module."""
    return Massdrop()