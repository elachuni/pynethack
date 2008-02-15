from nethack import NetHackPlayer

W = 80
H = 21

class VeryDumbPlayer (NetHackPlayer):
    """ Walk around in circles bumping in to walls like a wind-up toy """
    initialRole = "Priest"
    initialRace = "Elf"
    initialGender = "Random"

    def run(self):
        directions = ["N", "E", "S", "W"]
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
                if item.category == 'Comestibles':
                    self.eat(item)
                else:
                    self.quaff(item)
        self.sit()
        self.child.interact()

class Introspective (NetHackPlayer):
    """ I just print out all my stats and exit """
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

class Explorer (NetHackPlayer):
    """ I crawl the dungeon searching for stairs, and go down them """
    def __init__ (self, user=None, passwd=None, host=None):
        super (Explorer, self).__init__ (user, passwd, host)
        self.beenThere = [[False] * W for i in range(H)]
        self.reachable = [['Maybe'] * W for i in range(H)]
        dead = False

    def hasInspected (self, j, i):
        """ True if you've been in some cell adjacent to (j,i) -- ie you've been able to see what's there
            even if there's no light in the room (unless you're blind... we'll worry about that later)"""
        y = [j + 1, j + 1, j + 1, j, j - 1, j - 1, j - 1, j, j]
        x = [i - 1, i, i + 1, i + 1, i + 1, i, i - 1, i - 1, i]
        result = False
        for idx in range(len(y)):
            if 0 <= y[idx] and y[idx] < H and 0 <= x[idx] and x[idx] < W:
                if self.beenThere[y[idx]][x[idx]]:
                    result = True
        return result

    def somethingToExploreAt (self, j, i):
        """ True if some cell surrounding (j, i) may be reachable """
        y = [j + 1, j + 1, j + 1, j, j - 1, j - 1, j - 1, j]
        x = [i - 1, i, i + 1, i + 1, i + 1, i, i - 1, i - 1]
        result = False
        for idx in range(len(y)):
            if 0 <= y[idx] and y[idx] < H and 0 <= x[idx] and x[idx] < W:
                if self.reachable[y[idx]][x[idx]] == 'Maybe':
                    result = True
        return result

    def reachableDistance (self, j, i):
        """ Returns a full matrix of distances with 'graph', starting from ('j', 'i'),
            traveling only along reachable squares """
        dy = [1, 0, -1, 0]
        dx = [0, 1, 0, -1]
        distances = [[-1] * W for row in range(H)]
        distances[j][i] = 0
        stack = [(j, i)]
        while len(stack):
            y, x = stack.pop()
            for idx in range(len(dx)):
                if distances[y+dy[idx]][x+dx[idx]] == -1 and self.reachable[y+dy[idx]][x+dx[idx]] == 'Yes':
                    distances[y+dy[idx]][x+dx[idx]] = distances[y][x] + 1
                    stack = [(y+dy[idx], x+dx[idx])] + stack
        return distances

    def normalExploratoryDecision (self):
        for j in range(H):
            for i in range(W):
                if self.look(i, j).char in r'.#?\dfkx@+><}]': # Floor and stuff lying there
                    self.reachable[j][i] = 'Yes'
                elif self.beenThere[j][i]:
                    self.reachable[j][i] = 'Yes'
                elif self.look(i, j).char in '-|':
                    if self.look(i, j).foreground == 9: # Walls
                        self.reachable[j][i] = 'No'
                    else: # Open doors
                        self.reachable[j][i] = 'Yes'
                elif self.look(i, j).char == ' ':
                    if self.hasInspected (j,i):
                        self.reachable[j][i] = 'No'
        interesting = [[0] * W for i in range(H)]
        for j in range(H):
            for i in range(W):
                if self.reachable[j][i] == 'Yes' and not self.beenThere[j][i] and self.somethingToExploreAt (j, i):
                    interesting[j][i] = 1
        sites = [(j, i) for j in range(H) for i in range(W) if interesting[j][i]]
        if len(sites) == 0:
            return None
        distances = self.reachableDistance (self.y(), self.x())
        sites = [site for site in sites if distances[site[0]][site[1]] > 0]
        if len(sites) == 0:
            return None
        best = sites[0]
        for site in sites:
            if distances[site[0]][site[1]] < distances[best[0]][best[1]]:
                best = site
        return best

    def shortestPath (self, j, i):
        """ Returns the shortest path to (j, i) along reachable cells. """
        pos = (j, i)
        dx = [-1, 0, 1, 0]
        dy = [0, 1, 0, -1]
        while distance:
            pass
    def run (self):
        target = None
        while not dead:
            self.beenThere [self.y()][self.x()] = True
            if not target is None and target[0] == self.y() and target[1] == self.x(): # We've reached our target
                target = None
            if target is None:
                target = self.normalExploratoryDecision (self)
            #path = self.shortestPath (target[0], target[1])
            