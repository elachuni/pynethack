from nethack import NetHackPlayer

class VeryDumbPlayer (NetHackPlayer):
    """ Walk around in circles bumping in to walls like a wind-up toy """
    user = "dumb"
    passwd = "********"
    initialRole = "Priest"
    initialRace = "Elf"
    initialGender = "Random"

    def run(self):
        directions = ["North", "East", "South", "West"]
        direction = 0
        posX = self.screen.cursorX
        posY = self.screen.cursorY
        for i in range(40):
            print "Info:", self.info
            self.go (directions[direction])
            if self.screen.cursorX == posX and self.screen.cursorY == posY:
                #print "Changing direction as we're still at", posX, posY
                direction = (direction + 1) % 4
            posX = self.screen.cursorX
            posY = self.screen.cursorY
        self.child.interact()

class Barney (NetHackPlayer):
    """ I drink and eat all I can and then take a rest. """
    user = "dumb"
    passwd = "********"
    initialRole = "Wizard"
    initialGender = "Random"
    initialRace = "Random"
    initialAlignment = "Random"

    def run(self):
        done = False
        while not done:
            goodies = self.inventory(categories=['Potions', 'Comestibles'])
            if len(goodies) == 0:
                done = True
            else:
                item = goodies[0]
                if item['category'] == 'Comestibles':
                    self.eat(item)
                else:
                    self.quaff(item)
        self.sit()
        self.child.interact()

class Introspective (NetHackPlayer):
    """ I just print out all my stats and exit """
    user = "dumb"
    passwd = "********"
    def run (self):
        print "My Stats:"
        print "Strength:", self.strength()
        print "Dexterity:", self.dexterity()
        print "Constitution:", self.constitution()
        print "Intelligence:", self.intelligence()
        print "Wisdom:", self.wisdom()
        print "Charisma:", self.charisma()
        print "Alignment:", self.alignment()
        print "Hit points:", self.hitPoints()
        print "MaxHitPoints:", self.maxHitPoints()
        print "Gold:", self.gold()
        print "Dungeon Level:", self.dungeonLevel()
        print "Power:", self.power()
        print "Max Power:", self.maxPower()
        print "Armour Class:", self.armourClass()
        print "Experience Level:", self.experienceLevel()
        print "Experience:", self.experience()
        print "Turn:", self.turn()
        print "Hunger Status:", self.hungerStatus()
        print "Confused:", self.confused()
        print "Stunned:", self.stunned()
        print "Food poisoned:", self.foodPoisoned()
        print "Ill:", self.ill()
        print "Blind:", self.blind()
        print "Hallucinating:", self.hallucinating()
        print "Slimed:", self.slimed()
        print "Encumbrance:", self.encumbrance()
