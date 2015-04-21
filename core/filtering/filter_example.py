from core.BaseClass import Base


class Concrete(Base):

    def __init__(self):
        pass

    def information_of_interest(self, string):
        pass

    def logical_features(self):
        pass

    def update_procedure(self, thing_id):
        pass

c = Concrete()
c.integrity_check()