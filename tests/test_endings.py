import unittest
import sys
sys.path.append('..')

from nethack.examples import Explorer, Barney
from nethack.interactions import YesNoQuitInteraction
from nethack.connection import LocalNetHackConnection

class TestEndings(unittest.TestCase):
    def test_quit(self):
        conn = LocalNetHackConnection()
        np = Explorer(conn)
        np.play()
        i = np.quit()
        while not isinstance(i, YesNoQuitInteraction):
            i = i.answer('Yes')
        i = i.answer('quit')

    def test_die(self):
        conn = LocalNetHackConnection()
        np = Barney(conn)
        np.play()
        np.run()

    def test_save(self):
        conn = LocalNetHackConnection()
        np = Explorer(conn)
        np.play()
        i = np.save()
        
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestEndings))
    return suite

if __name__ == '__main__':
    unittest.main()

