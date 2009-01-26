from interactions import YesNoInteraction, YesNoQuitInteraction, Information

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
    initialRole = "Archeologist"
    initialGender = "Random"
    initialRace = "Random"
    initialAlignment = "Random"

    def run(self):
        done = False
        while not done:
            if self.server.pendingInteraction is not None:
                p = self.server.pendingInteraction
                if isinstance(p, YesNoInteraction):
                    if p.question == 'Stop eating?':
                        p.answer('no')
                        continue
                elif isinstance(p, YesNoQuitInteraction):
                    # Oops, we must have ate too much
                    p.answer('q')
                    done = True
                    continue
            goodies = self.inventory(categories=['Potions', 'Comestibles'])
            for item in goodies.values():
                if item.category == 'Comestibles':
                    self.eat(item)
                else:
                    self.quaff(item)
                break
            else:
                self.sit()
                done = True

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

class LevelStuff (object):
    def __init__(self):
        self.beenThere = [[False] * W for i in range(H)]
        self.reachable = [['Maybe'] * W for i in range(H)]
        self.searched = [[0] * W for i in range(H)]

class Explorer (NetHackPlayer):
    """ I crawl the dungeon searching for stairs, and go down them """
    dx = {'N':0,'NW':-1,'W':-1,'SW':-1,'S':0,'SE':1,'E':1,'NE':1}
    dy = {'N':-1,'NW':-1,'W':0,'SW':1,'S':1,'SE':1,'E':0,'NE':-1}

    initialRole = 'Barbarian' # Good class for really dumb bots

    def __init__ (self, server):
        super (Explorer, self).__init__ (server)
        self.levelStuffs = {}
        dead = False

    def hasInspected (self, y, x):
        """ True if you've been in some cell adjacent to (y,x) -- ie you've been able to see what's there
            even if there's no light in the room (unless you're blind... we'll worry about that later)"""
        result = False
        for d in self.dy.keys():
            if 0 <= y+self.dy[d] and y+self.dy[d] < H and 0 <= x+self.dx[d] and x+self.dx[d] < W:
                if self.beenThere[y+self.dy[d]][x+self.dx[d]]:
                    result = True
        return result

    def somethingToExploreAt (self, y, x):
        """ True if some cell surrounding (j, i) may be reachable """
        result = False
        for d in self.dy.keys():
            if 0 <= y+self.dy[d] and y+self.dy[d] < H and 0 <= x+self.dx[d] and x+self.dx[d] < W:
                if self.reachable[y+self.dy[d]][x+self.dx[d]] == 'Maybe':
                    result = True
        return result

    def reachableDistance (self, j, i):
        """ Calculates a full matrix of distances with 'graph', starting from ('j', 'i'),
            traveling only along reachable squares """
        self.distances = [[-1] * W for row in range(H)]
        self.distances[j][i] = 0
        stack = [(j, i)]
        while len(stack):
            y, x = stack.pop()
            for d in self.dx.keys():
                if self.distances[y+self.dy[d]][x+self.dx[d]] == -1 and self.reachable[y+self.dy[d]][x+self.dx[d]] == 'Yes':
                    self.distances[y+self.dy[d]][x+self.dx[d]] = self.distances[y][x] + 1
                    stack = [(y+self.dy[d], x+self.dx[d])] + stack

    def normalExploratoryDecision (self):
        for j in range(H):
            for i in range(W):
                if self.look(i, j).char in r'.#?\dfkx@+><%$(}][{):!"`/_': # Floor and stuff lying there
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
                if self.look(i, j).char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ:@&;' and not self.look(i, j).inverse: # Monsters are interesting
                    interesting[j][i] = 1
                if self.reachable[j][i] == 'Yes' and not self.beenThere[j][i] and self.somethingToExploreAt (j, i):
                    interesting[j][i] = 1
                elif self.look (i, j).char == '>':
                    interesting[j][i] = 2
        sites = [(j, i) for j in range(H) for i in range(W) if interesting[j][i]]
        if len(sites) == 0:
            return None
        self.reachableDistance (self.y(), self.x())
        sites = [site for site in sites if self.distances[site[0]][site[1]] > 0]
        if len(sites) == 0:
            return None
        best = sites[0]
        for site in sites:
            if (interesting[site[0]][site[1]] > interesting[best[0]][best[1]] or
              (interesting[site[0]][site[1]] == interesting[best[0]][best[1]] and
              self.distances[site[0]][site[1]] < self.distances[best[0]][best[1]])):
                best = site
        curY, curX = best
        while self.distances[curY][curX] > 0:
            for d in self.dx.keys():
                if 0 <= curY-self.dy[d] and curY-self.dy[d] < H and 0 <= curX-self.dx[d] and curX-self.dx[d] < W:
                    dist = self.distances[curY-self.dy[d]][curX-self.dx[d]]
                    if dist >= 0 and dist < self.distances[curY][curX]:
                        curY = curY-self.dy[d]
                        curX = curX-self.dx[d]
                        if self.distances[curY][curX] == 0:
                            return d
                        break

    def searchingExploratoryDecision (self):
        pass
    def nextToClosedDoor(self):
        """ Returns the direction in which a closed door is if I'm standing next to a door,
            or None."""
        x = self.x()
        y = self.y()
        for d in self.dx.keys():
            cell = self.look(x + self.dx[d], y + self.dy[d])
            if cell.char == '+' and cell.foreground == 3:
                return d

    def nextToMonster(self):
        """ Returns the direction in which a monster is if I'm standing next to a monster,
            or None."""
        x = self.x()
        y = self.y()
        for d in self.dx.keys():
            cell = self.look(x + self.dx[d], y + self.dy[d])
            if cell.char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ:@&;' and not cell.inverse:
                return d
            elif cell.char == '~' and not cell.foreground == 2:
                return d

    def setLevelStuffFromDungeonLevel(self):
        dlevel = str(self.dungeonLevel())
        if not self.levelStuffs.has_key (dlevel):
            self.levelStuffs[dlevel] = LevelStuff()
        lStuff = self.levelStuffs[dlevel]
        self.beenThere = lStuff.beenThere
        self.reachable = lStuff.reachable
        self.searched = lStuff.searched
    

    def run (self):
        dead = False
        previousPos = None
        target = None
        atNextPos = None
        while not dead:
            self.setLevelStuffFromDungeonLevel()
            moved = False
            self.beenThere [self.y()][self.x()] = True
            monster = self.nextToMonster()
            if monster:
                print "Monster towards the", monster
                msg = self.go (monster)
                moved = True
            door = self.nextToClosedDoor()
            if not moved and door:
                print "Door towards the", door
                msg = self.kick (door)
                moved = True
            if not moved and atNextPos == '>':
                msg = self.go ('D')
                moved = True
                atNextPos = None
            if not moved:
                previousPos = (self.x(), self.y())
                d = self.normalExploratoryDecision ()
                if d is None:
                    # We seem to have crawled the whole dungeon level, we'll have to search
                    d = self.searchingExploratoryDecision ()
                    raise ValueError, "I'm lost :("
                if not atNextPos is None and len(d) == 2:
                    if atNextPos in '|-': # You can't leave doorways diagonally
                        d = atNextPos == '|' and d[1] or d[0]
                target = (self.y()+self.dy[d], self.x()+self.dx[d])
                atNextPos = self.look (target[1],target[0]).char
                if len(d) == 2 and atNextPos in '|-': # You can't enter doorways diagonally
                    d = atNextPos == '|' and d[1] or d[0]
                msg = self.go (d)
                moved = True

            if isinstance (msg, YesNoQuitInteraction) and 'Do you want your possessions identified?' in msg.message:
                dead = True
            elif isinstance (msg, Information) and 'You try to move the boulder' in msg.message[0]:
                # Just don't try again
                self.beenThere[target[0]][target[1]] = True
            else:
                print isinstance(msg, Information), isinstance(msg, Information) and msg.message
if __name__ == '__main__':
    e = Explorer()
    e.play()
    e.run()
