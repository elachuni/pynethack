# Test the watching abilities of the connection.
import unittest
import sys
sys.path.append('..')

from nethack.connection import NetHackConnection
from nethack.scraper import Screen, Cell

from nethack.interactions import YesNoInteraction, YesNoQuitInteraction, SelectInteraction, SelectDialogInteraction, DirectionInteraction

class MockChild(object):
    def __init__(self, returnValue=1):
        self.returnValue = returnValue
        self.before = ''
        self.after = ''
    def expect(self, patterns, timeout):
        return self.returnValue



class Screenshot(Screen):
    """ A Screen that loads what it's showing from a file """
    def __init__ (self, filename):
        super(Screenshot, self).__init__()
        self.setScreen(filename)
    def setScreen(self, filename, rowOffset=0):
        f = open(filename)
        for i in range(rowOffset): f.readline()
        y, x = [int(w) for w in f.readline().strip().split()]
        row = 0
        for line in f:
            col = 0
            for c in line:
                self.screen[row][col] = Cell(c)
                col += 1
            row += 1
            if row > 24: break
        self.cursorX = x
        self.cursorY = y

class TestNetHackConnection(NetHackConnection):
    def __init__(self, screen):
        super (TestNetHackConnection, self).__init__(screen)
        self.child = MockChild()

class SelectDialogConnection(NetHackConnection):
    def __init__(self, filename):
        super (SelectDialogConnection, self).__init__()
        self.screen = Screenshot(filename)
        self.child = MockChild()
        self.filename = filename
    def send(self, char):
        if char == '>':
            self.screen.setScreen(self.filename, 25)
        elif char == '<':
            self.screen.setScreen(self.filename)

class TestConnection (unittest.TestCase):
    def testYesNo(self):
        screen = Screenshot('screenshots/yesno.txt')
        conn = TestNetHackConnection(screen)
        match = conn.watch()
        self.assertEquals(YesNoInteraction, type(match))

    def testYesNoQuit(self):
        screen = Screenshot('screenshots/yesnoquit.txt')
        conn = TestNetHackConnection(screen)
        match = conn.watch()
        self.assertEquals(YesNoQuitInteraction, type(match))

    def testSelect(self):
        screen = Screenshot('screenshots/select.txt')
        conn = TestNetHackConnection(screen)
        match = conn.watch()
        self.assertEquals(SelectInteraction, type(match))

    def testDirection(self):
        screen = Screenshot('screenshots/direction.txt')
        conn = TestNetHackConnection(screen)
        match = conn.watch()
        self.assertEquals(DirectionInteraction, type(match))

    def testMultiSelect(self):
        conn = SelectDialogConnection('screenshots/multiSelectLoot.txt')
        match = conn.watch()
        self.assertEquals(SelectDialogInteraction, type(match))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestConnection))
    return suite

if __name__ == '__main__':
    unittest.main()
