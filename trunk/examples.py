from nethack import NetHackPlayer

class VeryDumbPlayer (NetHackPlayer):
    """ Walk around in circles bumping in to walls like a wind-up toy """
    user = "dumb"
    passwd = "********"
    role = "Priest"
    race = "Elf"
    gender = "Random"

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
    role = "Wizard"
    gender = "Random"
    race = "Random"
    alignment = "Random"

    def run(self):
        done = False
        print "My Stats:"
        print "Strength:", self.myStr()
        print "Dexterity:", self.myDex()
        print "Constitution:", self.myCon()
        print "Intelligence:", self.myInt()
        print "Wisdom:", self.myWis()
        print "Charisma:", self.myCha()
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
