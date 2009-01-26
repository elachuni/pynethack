import sys
import unittest

sys.path.append('..')
from nethack.serialize import unserialize

class TestBasicFunctions (unittest.TestCase):
    def setUp(self):
        self.np = unserialize('scenarios/basic.nh')
        self.np.server.echo = False
    def tearDown(self):
        self.np.quit()
    def testBeingWorn(self):
        inv = self.np.inventory()
        self.assertTrue(inv['b'].beingWorn())
    def testWielded(self):
        inv = self.np.inventory()
        self.assertTrue(inv['a'].wielded())
    def testBUC(self):
        inv = self.np.inventory()
        self.assertEquals('blessed', inv['a'].buc())
        self.assertEquals('uncursed', inv['b'].buc())
        self.assertEquals('unknown', inv['c'].buc())


if __name__ == '__main__':
    unittest.main()

