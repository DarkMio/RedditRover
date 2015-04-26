from core.BaseClass import Base


class FilterExampleFull(Base):

    def __init__(self):
        super().__init__()
        self.DESCRIPTION = "Sampletext"
        self.PASSWORD = "testpwd"
        self.USERNAME = "testuser"
        self.REGEX = r'string'

    def information_of_interest(self, string):
        pass

    def logical_features(self):
        pass

    def update_procedure(self, thing_id):
        pass


def init():
    """Init Call from module importer to return only the object itself, rather than the module."""
    return FilterExampleFull()