from core.BaseClass import Base


class FilterExample(Base):

    def __init__(self):
        super().__init__()

    def execute_comment(self, comment):
        pass

    def execute_submission(self, submission):
        pass

    def update_procedure(self, thing_id):
        pass


def init():
    """Init Call from module importer to return only the object itself, rather than the module."""
    return FilterExample()