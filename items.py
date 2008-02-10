
class Item (object):
    def __init__ (self, key, description=None, category=None):
        self.key = key
        self.description = description
        self.category = category
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.description)

