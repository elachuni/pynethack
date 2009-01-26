# Test the watching abilities of the connection.
import unittest
import sys
sys.path.append('..')

from nethack.connection import NetHackConnection
from nethack.scraper import Screen, Cell

from nethack.interactions import YesNoInteraction, YesNoQuitInteraction, SelectInteraction, DirectionInteraction

class MockChild(object):
    def __init__(self, returnValue=1):
        self.returnValue = returnValue
        self.before = ''
        self.after = ''
    def expect(self, patterns, timeout):
        return self.returnValue

class Screenshot(Screen):
    """ A Screen that loads what it's showing from a file """
    def __init__ (self, filename, y, x):
        super(Screenshot, self).__init__()
        f = open(filename)
        row = 0
        for line in f:
            col = 0
            for c in line:
                self.screen[row][col] = Cell(c)
                col += 1
            row += 1
        self.cursorX = x
        self.cursorY = y

class TestNetHackConnection(NetHackConnection):
    def __init__(self, screen):
        super (TestNetHackConnection, self).__init__(screen)
        self.child = MockChild()

class TestConnection (unittest.TestCase):
    def testYesNo(self):
        screen = Screenshot('screenshots/yesno.txt', 0, 39)
        conn = TestNetHackConnection(screen)
        match = conn.watch()
        self.assertEquals(YesNoInteraction, type(match))

    def testYesNoQuit(self):
        screen = Screenshot('screenshots/yesnoquit.txt', 0, 50)
        conn = TestNetHackConnection(screen)
        match = conn.watch()
        self.assertEquals(YesNoQuitInteraction, type(match))

    def testSelect(self):
        screen = Screenshot('screenshots/select.txt', 0, 37)
        conn = TestNetHackConnection(screen)
        match = conn.watch()
        self.assertEquals(SelectInteraction, type(match))

    def testDirection(self):
        screen = Screenshot('screenshots/direction.txt', 0, 20)
        conn = TestNetHackConnection(screen)
        match = conn.watch()
        self.assertEquals(DirectionInteraction, type(match))


if __name__ == '__main__':
    unittest.main()
