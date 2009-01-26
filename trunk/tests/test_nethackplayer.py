import sys
import unittest

sys.path.append('..')
from nethack.serialize import unserialize

class TestBasicFunctions (unittest.TestCase):
    def setUp(self):
        self.np = unserialize('scenarios/basic.nh')
        self.np.server.echo = False
    def tearDown(self):
        if self.np.server.pendingInteraction:
            self.np.server.pendingInteraction.answerDefault()
        self.np.quit()
    def testAttrs(self):
        self.assertEquals(9, self.np.strength())
        self.assertEquals(14, self.np.dexterity())
        self.assertEquals(12, self.np.constitution())
        self.assertEquals(18, self.np.intelligence())
        self.assertEquals(9, self.np.wisdom())
        self.assertEquals(13, self.np.charisma())
    def testOther(self):
        self.assertEquals('Neutral', self.np.alignment())
        self.assertEquals(12, self.np.hitPoints())
        self.assertEquals(12, self.np.maxHitPoints())
        self.assertEquals(0, self.np.gold())
        self.assertEquals(1, self.np.dungeonLevel())
        self.assertEquals(8, self.np.power())
        self.assertEquals(8, self.np.maxPower())
        self.assertEquals(9, self.np.armourClass())
        self.assertEquals(1, self.np.experienceLevel())
        self.assertEquals(1, self.np.experienceLevel())
        self.assertEquals('Not Hungry', self.np.hungerStatus())
        self.assertEquals(False, self.np.confused())
        self.assertEquals(False, self.np.stunned())
        self.assertEquals(False, self.np.foodPoisoned())
        self.assertEquals(False, self.np.ill())
        self.assertEquals(False, self.np.blind())
        self.assertEquals(False, self.np.hallucinating())
        self.assertEquals(False, self.np.slimed())
        self.assertEquals(48, self.np.x())
        self.assertEquals(16, self.np.y())
    def testEncumbrance(self):
        self.assertEquals('Unencumbered', self.np.encumbrance())
        self.np.go('W')
        self.np.go('W')
        self.np.pickUp()
        self.assertEquals('Burdened', self.np.encumbrance())

    def testInventory(self):
        inv = self.np.inventory()
        self.assertEquals(14, len(inv))
        self.np.go('W')
        self.np.go('W')
        m = self.np.loot()
        m = m.answer(m.options)
        inv = self.np.inventory()
        self.assertEquals(16, len(inv))

    def testLoot(self):
        self.np.go('W')
        self.np.go('W')
        m = self.np.loot()
        m = m.answer(m.options)
        m = self.np.loot()
        m = self.np.loot(takeOut=False)
        self.assertEquals(16, len(m.options))
        m.answer(m.options[-4:])
        m = self.np.loot()
        self.assertEquals(4, len(m.options))
        m.answerDefault()

    def testClothes(self):
        self.assertRaises(ValueError, self.np.takeOff, 'b')
        info = self.np.takeOff(self.np.inventory()['b'])
        self.assertTrue('You were wearing' in info.message[0])
        self.assertRaises(ValueError, self.np.wear, 'b')
        info = self.np.wear(self.np.inventory()['b'])
        self.assertTrue('You are now wearing' in info.message[0])

class TestFood (unittest.TestCase):
    def setUp(self):
        self.np = unserialize('scenarios/food.nh')
        self.np.server.echo = False
    def tearDown(self):
        if self.np.server.pendingInteraction:
            self.np.server.pendingInteraction.answerDefault()
        self.np.quit()
    def testFood(self):
        food = self.np.inventory('Comestibles').keys()[0]
        self.assertRaises(ValueError, self.np.eat, food)
        info = self.np.eat(self.np.inventory()[food])
        self.assertTrue('Core dumped' in info.message[0])

class TestDrink (unittest.TestCase):
    def setUp(self):
        self.np = unserialize('scenarios/fountain.nh')
        self.np.server.echo = False
    def tearDown(self):
        while self.np.server.pendingInteraction:
            self.np.server.pendingInteraction.answerDefault()
        self.np.quit()
    def testDrink(self):
        drink = self.np.inventory('Potions').values()[0]
        self.assertRaises(ValueError, self.np.quaff, drink.key)
        q = self.np.quaff(drink) # Drink from the fountain?
        info = q.answer('y')
        self.np.go('S')
        self.np.quaff(drink)
        

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBasicFunctions))
    suite.addTest(unittest.makeSuite(TestFood))
    suite.addTest(unittest.makeSuite(TestDrink))
    return suite

if __name__ == '__main__':
    unittest.main()
