
class Item (object):
    def __init__ (self, key, description=None, category=None):
        self.key = key
        self.description = description
        self.category = category
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.description)

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

