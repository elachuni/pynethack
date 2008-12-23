import unittest
import sys
sys.path.append('..')

from examples import Explorer, Barney
from interactions import YesNoQuitInteraction
class TestEndings(unittest.TestCase):
    def test_quit(self):
        np = Explorer()
        np.play()
        i = np.quit()
        while not isinstance(i, YesNoQuitInteraction):
            i = i.answer('Yes')
        i = i.answer('quit')

    def test_die(self):
        np = Barney()
        np.play()
        np.run()

    def test_save(self):
        np = Explorer()
        np.play()
        i = np.save()
        
if __name__ == '__main__':
    unittest.main()

