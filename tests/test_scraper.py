import unittest
import sys
import re
sys.path.append('..')

from nethack.scraper import WIDTH, HEIGHT, Screen

class TestScraper(unittest.TestCase):
    def test_init(self):
        sc = Screen()
        self.assertEquals(sc.getArea(), [' ' * WIDTH for i in range(HEIGHT)])
        self.assertEquals(sc.cursorX, 0)
        self.assertEquals(sc.cursorY, 0)
        self.assertEquals(sc.savedCursorX, 0)
        self.assertEquals(sc.savedCursorY, 0)
        self.assertEquals(sc.charSet, "default")
        self.assertEquals(sc.G0, "default")
        self.assertEquals(sc.G1, "default")
        self.assertEquals(sc.charAttBold, False)
        self.assertEquals(sc.charAttInverse, False)
        self.assertEquals(sc.charAttForeground, 9)

    def test_printstr(self):
        msg = "Hello World!"
        sc = Screen()
        sc.printstr(msg)
        self.assert_(sc.getRow(0).startswith(msg))
        sc.printstr('\x1b[H') # Goto Home
        self.assertEquals(sc.getCharAtRelativePos(), 'H')
        sc.printstr('\x1b[2J') # Clear Screen
        self.assertEquals(sc.getRow(0), ' ' * WIDTH)
        sc.printstr('\x1b[5d') # Goto row 5
        self.assertEquals(sc.cursorY, 4)
        sc.printstr('\x1b7') # Save cursor
        sc.printstr('\x1b[6;5H') # Goto row 6, column 5
        self.assertEquals(sc.cursorY, 5)
        self.assertEquals(sc.cursorX, 4)
        sc.printstr('\x1b8') # Restore cursor
        self.assertEquals(sc.cursorY, 4)
        self.assertEquals(sc.cursorX, 0)
        sc.printstr('\x1b[C') # cursor Right
        self.assertEquals(sc.cursorY, 4)
        self.assertEquals(sc.cursorX, 1)
        sc.printstr('\x1b[A') # cursor Up
        self.assertEquals(sc.cursorY, 3)
        self.assertEquals(sc.cursorX, 1)
        sc.printstr(msg)
        sc.printstr('\x1b[4;0H') # Goto row 4, column 1
        sc.printstr('\x1b[K') # erase to the end of the line
        self.assertEquals(sc.getRow(4), ' ' * WIDTH)
        sc.printstr('\x1b(B') # Set G0 charset
        self.assertEquals(sc.G0, 'usascii')
        sc.printstr('\x1b)0') # Set G1 charset
        self.assertEquals(sc.G1, 'dec')

    def test_gotoHome(self):
        msg = "Hello World!"
        sc = Screen()
        sc.printstr(msg)
        sc.gotoHome(re.match(r'\[H', '[H'))
        self.assertEquals(sc.getCharAtRelativePos(), 'H')

    def test_clearScreen(self):
        msg = "Hello World!"
        sc = Screen()
        sc.printstr(msg)
        sc.clearScreen('[2J')
        self.assertEquals(sc.getRow(0), ' ' * WIDTH)

    def test_gotoY (self):
        sc = Screen()
        sc.gotoY(re.match(r'\[(\d+)d', '[7d'))
        self.assertEquals(sc.cursorY, 6)

    def test_gotoXY (self):
        sc = Screen()
        sc.gotoXY(re.match(r'\[(\d+);(\d+)H', '[3;10H'))
        self.assertEquals(sc.cursorY, 2)
        self.assertEquals(sc.cursorX, 9)

    def test_saveCursor_restoreCursor (self):
        sc = Screen()
        sc.gotoXY(re.match(r'\[(\d+);(\d+)H', '[3;10H'))
        sc.saveCursor('')
        self.assertEquals(sc.savedCursorY, 2)
        self.assertEquals(sc.savedCursorX, 9)
        sc.gotoXY(re.match(r'\[(\d+);(\d+)H', '[11;30H'))
        self.assertEquals(sc.cursorY, 10)
        self.assertEquals(sc.cursorX, 29)
        sc.restoreCursor('')
        self.assertEquals(sc.cursorY, 2)
        self.assertEquals(sc.cursorX, 9)

    def test_cursorRight (self):
        sc = Screen()
        sc.cursorRight('[C')
        self.assertEquals(sc.cursorY, 0)
        self.assertEquals(sc.cursorX, 1)

    def test_cursorUp (self):
        sc = Screen()
        sc.gotoXY(re.match(r'\[(\d+);(\d+)H', '[3;10H'))
        sc.cursorUp('[A')
        self.assertEquals(sc.cursorY, 1)
        self.assertEquals(sc.cursorX, 9)

    def test_eraseToEndOfLine (self):
        msg = "Hello World!"
        sc = Screen()
        sc.printstr(msg)
        sc.gotoHome('[H')
        sc.eraseToEndOfLine('[K')
        self.assertEquals(sc.getRow(0), ' ' * WIDTH)

    def test_setCharset(self):
        sc = Screen()
        sc.setCharset(re.match(r'(\()(.)', '(B'))
        self.assertEquals(sc.G0, 'usascii')
        sc.setCharset(re.match(r'(\()(.)', '(0'))
        self.assertEquals(sc.G0, 'dec')
        sc.setCharset(re.match(r'(\))(.)', ')B'))
        self.assertEquals(sc.G1, 'usascii')
        sc.setCharset(re.match(r'(\))(.)', ')0'))
        self.assertEquals(sc.G1, 'dec')

    def test_setCharacterAtts(self):
        sc = Screen()
        sc.setCharacterAtts (re.match(r'\[(\d+)m', '[7m'))
        self.assertEquals(sc.charAttInverse, True)
        sc.setCharacterAtts (re.match(r'\[(\d+)m', '[32m'))
        self.assertEquals(sc.charAttForeground, 2)
        sc.setCharacterAtts (re.match(r'\[(\d+)m', '[1m'))
        self.assertEquals(sc.charAttBold, True)
        sc.resetCharAtts(re.match(r'\[m', '[m'))
        self.assertEquals(sc.charAttBold, False)
        self.assertEquals(sc.charAttInverse, False)
        self.assertEquals(sc.charAttForeground, 9)

    def test_ignored(self):
        sc = Screen()
        sc.printstr('\x1b[?1049h')
        sc.printstr('\x1b[?1049l')
        sc.printstr('\x1b[1049l')

    def test_matchMultiSelectMarker (self):
        sc = Screen()
        sc.printstr('\x1b[24;1H (1 of 2) ')
        self.assertTrue (sc.matches (r'\(end\) |\(\d of \d\) '))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestScraper))
    return suite

if __name__ == "__main__":
    unittest.main()
