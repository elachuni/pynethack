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
    def testBCU(self):
        inv = self.np.inventory()
        self.assertEquals('blessed', inv['a'].bcu())
        self.assertEquals('uncursed', inv['b'].bcu())
        self.assertEquals('unknown', inv['c'].bcu())

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBasicFunctions))
    return suite

if __name__ == '__main__':
    unittest.main()

