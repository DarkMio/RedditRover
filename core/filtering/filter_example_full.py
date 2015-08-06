from core.BaseClass import Base


class FilterExampleFull(Base):

    def __init__(self):
        super().__init__()
        self.DESCRIPTION = "Sampletext"
        self.PASSWORD = "testpwd"
        self.USERNAME = "testuser"
        self.REGEX = r'string'

    def execute_comment(self, comment):
        pass

    def execute_titlepost(self, title_only):
        pass

    def execute_link(self, link_submission):
        pass

    def execute_submission(self, submission):
        pass

    def update_procedure(self, thing_id):
        pass


def init():
    """Init Call from module importer to return only the object itself, rather than the module."""
    return FilterExampleFull()
