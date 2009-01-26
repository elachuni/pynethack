
class Item (object):
    def __init__ (self, key, description=None, category=None):
        self.key = key
        self.description = description
        self.category = category
    def __repr__(self):
        description = self.key
        if not self.description is None:
            description = self.description
        return '<%s %s>' % (self.__class__.__name__, description)
    def beingWorn(self):
        return '(being worn)' in self.description
    def wielded(self):
        return '(weapon in hands)' in self.description
    def rusty(self):
        return 'rusty' in self.description
    def buc(self):
        """ Return the blessed/uncursed/cursed status """
        for stat in ['blessed', 'uncursed', 'cursed']:
            if stat in self.description:
                return stat
        return 'unknown'

class Spell (object):
    def __init__ (self, key, description=None, headings=None):
        self.key = key
        self.description = description
        print "Key:", key
        print "Desc:", description
        if not headings is None:
            levelPos = headings.find('Level')
            categoryPos = headings.find('Category')
            failPos = headings.find('Fail')
            print "LevelPos:", levelPos
            print "CatPos:", categoryPos
            print "FailPos:", failPos
            self.name = self.description[:levelPos].strip()
            self.level = int(self.description[levelPos:categoryPos].strip())
            self.category = self.description[categoryPos:failPos].strip()
            self.fail = int(self.description[failPos:].strip(' %'))
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.description)

