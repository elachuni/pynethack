#!/usr/bin/python

# PyNethack.  A library to allow you to write bots that play nethack
# Copyright (C) 2007  Anthony Lenton

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Run against DGameLaunch:
#    ftp://ftp.alt.org/pub/dgamelaunch/

import pexpect
from scraper import Screen
import nethackkeys as keys
import time
import sys
from interactions import checkPendingInteraction, YesNoInteraction, MultipleSelectInteraction

class NetHackPlayer(object):
    initialRole = "Random"
    initialRace = "Random"
    initialGender = "Random"
    initialAlignment = "Random"
    def __init__(self, user=None, passwd=None):
        self.child = pexpect.spawn ("telnet localhost")
        self.screen = Screen()
        self.lastSeenTurn = -1 # Used by 'watch', no need to change this
        self.pendingInteraction = None
        self.info = []
        if not user is None:
            self.user = user
        if not passwd is None:
            self.passwd = passwd

    def send (self, msg):
        """ Sends 'msg' down the wire. """
        checkPendingInteraction (self)
        self.child.send (msg)

    def sendline (self, msg):
        """ Sends 'msg' down the wire followed by a newline character. """
        checkPendingInteraction (self)
        self.child.sendline (msg)

    def login(self):
        """ Enter user/password credentials """
        self.watch ("=> ") # Welcome screen
        opts = self.parseOptions (") ", 1, 13, 40, 4)
        if opts.has_key ("login"):
            self.send (opts['login']) # attempt log in
        else:
            raise ValueError, "login called, but we're not at the welcome screen"
        self.watch ("=> ")
        self.sendline (self.user)
        self.watch ("=> ")
        if self.screen.getRow (9).strip() == 'There was a problem with your last entry.':
            raise ValueError, "invalid username"
        self.sendline (self.passwd)

    def new_game(self):
        """ Start a new game and select role, race, gender and alignment """
        self.watch ("=> ") # We should already be logged in
        opts = self.parseOptions (") ", 1, 13, 40, 6)
        if opts.has_key ("play nethack!"):
            self.send (opts['play nethack!']) # attempt log in
        else:
            raise ValueError, "new_game called, but we're not at the main menu"
        match = self.watch (['[ynq] ', 'in 1'])
        if match == '[ynq] ':
            self.send ('n')
        elif match == 'in 1':
            print "Waiting 10 seconds for old save game to be restored...\n"
            # Wait 10 seconds for old game to be restored
            time.sleep(11)
        self.watch ('(end) ')
        if self.screen.getRow(0).find('Role') >= 0:
            self.send(keys.roles[self.initialRole])
            self.watch ('(end) ')
        if self.screen.getRow(0).find('Race') >= 0:
            self.send(keys.races[self.initialRace])
            self.watch ('(end) ')
        if self.screen.getRow(0).find('Gender') >= 0:
            self.send(keys.genders[self.initialGender])
            self.watch ('(end) ')
        if self.screen.getRow(0).find('Alignment') >= 0:
            self.send(keys.alignments[self.initialAlignment])
            self.watch()

    def watch (self, expecting=None):
        """ Update the screen and see what happens. """
        if type(expecting) == type(''):
            expecting = [expecting]
        patterns = ['--More--', pexpect.TIMEOUT]
        matched = None
        info = []
        while matched is None:
            i = self.child.expect (patterns, timeout=0.5)
            self.screen.printstr(self.child.before)
            if self.child.after != pexpect.TIMEOUT:
                self.screen.printstr(self.child.after)
            if i == 0:
                # --More--
                if self.screen.cursorY == 0:
                    msg = self.screen.getRow(0, start=0, finish=self.screen.cursorX - 9).strip()
                else:
                    msg = self.screen.getArea(self.screen.cursorX - 9, 0, 80, self.screen.cursorY)
                info += [msg]
                self.send (' ')
            elif i == 1:
                # Timed out
                if self.screen.getRow (0)[:40] == 'Do you want your possessions identified?':
                    # You're dead... hand over control
                    self.child.interact()
                    sys.exit()
                elif not expecting is None:
                    matched = self.screen.multiMatch(expecting)
                if matched is None:
                    msg = self.screen.getRow(0).strip()
                    if len(msg) > 0:
                        info += [msg]
                    matched = '@'
                #if matched is None:
                    #print "Expecting", expecting
                    #print "Found '%s'" % self.screen.getRow (
                     #self.screen.cursorY, 0,
                     #self.screen.cursorX)
                    #print "Timed out with an unexpected output :-("
                    #self.screen.dump()
                    #print "Cursor at %d,%d" % (self.screen.cursorY, self.screen.cursorX)
                    #print "Output so far:", [self.child.before]
                    #print "Expecting:", patterns
                    #print "Happy hacking!"
                    #raise ValueError, "Unexpected Output"
            self.screen.dump()
        if self.turn() != self.lastSeenTurn:
            self.info = info
            self.cachedInventory = None
            self.lastSeenTurn = self.turn()
        else:
            self.info += info
        return matched

    def parseOptions (self, sep, x, y, w, h):
        """ Parse an area of the screen as a list of options. Used for menus only for now """
        lines = self.screen.getArea (x, y, w, h)
        splits = [line.split(sep) for line in lines]
        strips = [(opt[1].strip().lower(), opt[0].strip()) for opt in splits if len(opt) == 2]
        return dict(strips)

    def run (self):
        """ Redefine this method to give your bot a life! """
        self.child.interact()

    def go (self, direction):
        """ Walk one position in the specified direction.  Direction can be one of
            'N', 'North'
            'S', 'South'
            'W', 'West'
            'E', 'East'
            'NW', 'NorthWest'
            'NE', 'NorthEast'
            'SW', 'SouthWest'
            'SE', 'SouthEast'
            'D', 'Down'
            'U', 'Up'
            '.', 'Stay' (stay where you are and do nothing for one turn)
        """
        print "Going %s..." % direction
        self.send (keys.dirs[direction])
        self.watch()

    def openDoor (self, direction):
        """ Open a door in the specified direction.  See 'go' for list of possible directions. """
        self.send ('o')
        matched = self.watch('In what direction? ')
        if matched == 'In what direction? ':
            self.send (keys.dirs[direction])
            self.watch()

    def closeDoor (self, direction):
        """ Close a door in the specified direction.  See 'go' for list of possible directions. """
        self.send ('c')
        matched = self.watch('In what direction? ')
        if matched == 'In what direction? ':
            self.send (keys.dirs[direction])
            self.watch()

    def kick (self, direction):
        """ Kick in the specified direction.  See 'go' for a list of possible directions. """
        self.send ('\x04')
        matched = self.watch('In what direction? ')
        if matched == 'In what direction? ':
            self.send (keys.dirs[direction])
            self.watch()

    def fight (self, direction):
        """ Fight (even if you don't sense a monster) in the specified direction. """
        self.send ('F')
        self.send (keys.dirs[direction])
        self.watch()

    def quaff (self, potion):
        """ Quaff a potion.  'potion' should have been retrieved from our inventory recently. """
        print "Quaffing %s..." % potion['description']
        self.send ('q')
        matched = self.watch('] ')
        if matched == '] ':
            self.send (potion['key'])
            self.watch()

    def eat (self, food):
        """ Eat something. 'food' should have been retrieved from our inventory recently.
            An interaction might be returned if the game prompts to stop the meal before finishing.
        """
        print "Eating %s..." % food['description']
        self.send ('e')
        matched = self.watch('] ')
        if matched == '] ':
            self.send (food['key'])
            ev = self.watch('Stop eating? [yn] (y) ')
            if ev == 'Stop eating? [yn] (y) ':
                return YesNoInteraction (self, self.screen.getRow (0).strip())

    def sit (self):
        """ Sit down for one turn """
        print "Sitting"
        self.sendline ("#sit")
        self.watch()

    def drop (self, item, amount=None):
        """ Drop an item.  'item' should have been retrieved recently from our inventory.
            If 'amount' is an integer, drop that amount of items
            (to drop one gold piece, for example) """
        self.send ('d')
        if not amount is None:
            self.send (str(amount))
        self.send (item['key'])
        self.watch()

    def multiDrop (self, items):
        """ Drop multiple items. 'items' is a list of stuff from our inventory. """
        self.send ('D')
        self.sendline ('a') # All types
        more_pages = True
        while more_pages:
            matched = self.watch (['(end) ', '(1 of 2)', '(2 of 2)'])
            for i in items:
                self.send (i['key'])
            self.send (' ')
            if matched != '(1 of 2)':
                more_pages = False
        self.watch()

    def pickUp (self):
        """ Pick one or more items up off the ground.
            If only one item is available to be picked up, then it's automatically picked up.
            Else, an interaction is returned prompting the user to select between available items. """
        self.send (',')
        matched = self.watch (['(end) ', '(1 of 2)', '(2 of 2)'])
        if matched != '@':
            return MultipleSelectInteraction (self)

    def quit (self):
        """ Abandon this game """
        self.sendline ('#quit')
        matched = self.watch ('[yn] (n) ')
        if matched == '[yn] (n) ':
            return YesNoInteraction (self, self.screen.getRow (0).strip())


    def inventory (self, categories=None):
        """ Retrieve your inventory.  'categories' can be a list of strings describing the categories
            you want to restrict to, as "Weapons", "Potions", etc. """
        if self.cachedInventory is None:
            self.send ('i')
            more_pages = True
            self.cachedInventory = []
            while more_pages:
                matched = self.watch(['(end) ', '(1 of 2)', '(2 of 2)'])
                        # We need a bit more power in our patterns here!
                lines = self.screen.getArea (self.screen.cursorX - len(matched), 0, h=self.screen.cursorY)
                for line in lines:
                    if line.find(' - ') == -1:
                        category = line.strip()
                    else:
                        key, item = line.split(' - ', 1)
                        self.cachedInventory.append({'key': key.strip(),
                                                     'description':item.strip(),
                                                     'category': category})
                self.send (' ')
                if matched != '(1 of 2)':
                    more_pages = False
            self.watch()
        if categories is None:
            return self.cachedInventory
        else:
            return [item for item in self.cachedInventory if item['category'] in categories]

    def strength (self):
        """Returns my current strength.  For strength above 18 a floating point number is returned,
           as in 18/25 -> 18.25.  For 18/** return 19."""
        statLine = self.screen.getRow(22, start=23)
        st = statLine.find('St:') + 3
        if statLine[st:st+5] == '18/**': # Special case this one out
            return 19.0
        else:
            return float(statLine[st : statLine.find(' ', st + 1)].replace('/', '.'))

    def dexterity (self):
        """ Returns my current dexterity as an int """
        statLine = self.screen.getRow(22, start=23)
        dx = statLine.find('Dx:') + 3
        return int(statLine[dx : statLine.find (' ', dx + 1)])

    def constitution (self):
        """ Returns my current constitution as an int """
        statLine = self.screen.getRow (22, start=23)
        co = statLine.find('Co:') + 3
        return int(statLine[co : statLine.find (' ', co + 1)])

    def intelligence (self):
        """ Returns my current intelligence as an int """
        statLine = self.screen.getRow (22, start=23)
        val = statLine.find('In:') + 3
        return int(statLine[val : statLine.find (' ', val + 1)])

    def wisdom (self):
        """ Returns my current wisdom as an int """
        statLine = self.screen.getRow (22, start=23)
        wi = statLine.find('Wi:') + 3
        return int(statLine[wi : statLine.find (' ', wi + 1)])

    def charisma (self):
        """ Returns my current charisma as an int """
        statLine = self.screen.getRow (22, start=23)
        ch = statLine.find('Ch:') + 3
        return int(statLine[ch : statLine.find (' ', ch + 1)])

    def alignment (self):
        """ Returns my current alignment as a string: one of "Lawful", "Chaotic" or "Neutral" """
        statLine = self.screen.getRow (22, start=60)
        for align in keys.alignments.keys():
            if align in statLine:
                return align

    def hitPoints (self):
        """ Returns my current hit-points as an int """
        statLine = self.screen.getRow (23)
        hp = statLine.find ('HP:') + 3
        return int(statLine[hp : statLine.find ('(', hp + 1)])

    def maxHitPoints (self):
        """ Returns my current maximum hit-points as an int """
        statLine = self.screen.getRow (23)
        hp = statLine.find ('HP:') + 3
        hp = statLine.find ('(', hp) + 1
        return int(statLine[hp : statLine.find (')', hp + 1)])

    def gold (self):
        """ Returns the amount of gold in my purse, as an int """
        statLine = self.screen.getRow (23)
        val = statLine.find ('$:') + 2
        return int(statLine[val : statLine.find (' ', val + 1)])

    def dungeonLevel (self):
        """ Returns my current dungeon level as an int """
        statLine = self.screen.getRow (23)
        val = statLine.find ('Dlvl:') + 5
        return int(statLine[val : statLine.find (' ', val + 1)])

    def power (self):
        """ Returns my current power as an int """
        statLine = self.screen.getRow (23)
        val = statLine.find ('Pw:') + 3
        return int(statLine[val : statLine.find ('(', val + 1)])

    def maxPower (self):
        """ Returns my current maximum power as an int """
        statLine = self.screen.getRow (23)
        val = statLine.find ('Pw:') + 3
        val = statLine.find ('(', val) + 1
        return int(statLine[val : statLine.find (')', val + 1)])

    def armourClass (self):
        """ Returns my current armour class as an int """
        statLine = self.screen.getRow (23)
        val = statLine.find ('AC:') + 3
        return int(statLine[val : statLine.find (' ', val + 1)])

    def experienceLevel (self):
        """ Returns my current experience level as an int.  Compare with 'experience' """
        statLine = self.screen.getRow (23)
        val = statLine.find ('Xp:') + 3
        return int(statLine[val : statLine.find ('/', val + 1)])

    def experience (self):
        """ Returns my current dexterity as an int. Compare with 'experienceLevel' """
        statLine = self.screen.getRow (23)
        val = statLine.find ('Xp:') + 3
        val = statLine.find ('/', val) + 1
        return int(statLine[val : statLine.find (' ', val + 1)])

    def turn (self):
        """ Returns the contents of the turn counter as an int """
        statLine = self.screen.getRow (23)
        val = statLine.find ('T:') + 2
        if val == 1: # find returned -1
            return -1
        return int(statLine[val : statLine.find (' ', val + 1)])

    def hungerStatus (self):
        """ Returns my current hunger status as a string: one of "Satiated", "Not Hungry",
            "Hungry", "Weak", or "Fainting" """
        statLine = self.screen.getRow (23, start=40)
        for stat in ["Satitated", "Hungry", "Weak", "Fainting"]:
            if stat in statLine:
                return stat
        return "Not Hungry"

    def confused (self):
        """ Returns True if I'm currently confused """
        statLine = self.screen.getRow (23, start=50)
        return "Conf" in statLine

    def stunned (self):
        """ Returns True if I'm currently stunned """
        statLine = self.screen.getRow (23, start=50)
        return "Stun" in statLine

    def foodPoisoned (self):
        """ Returns True if I'm currently food poisoned """
        statLine = self.screen.getRow (23, start=50)
        return "FoodPois" in statLine

    def ill (self):
        """ Returns True if I'm currently ill """
        statLine = self.screen.getRow (23, start=50)
        return "Ill" in statLine

    def blind (self):
        """ Returns True if I'm currently blind """
        statLine = self.screen.getRow (23, start=50)
        return "Blind" in statLine

    def hallucinating (self):
        """ Returns True if I'm currently hallucinating """
        statLine = self.screen.getRow (23, start=50)
        return "Hallu" in statLine

    def slimed (self):
        """ Returns True if I'm currently turning in to a slime """
        statLine = self.screen.getRow (23, start=50)
        return "Slime" in statLine

    def encumbrance (self):
        """ Returns my current encumbrance status as a string: one of "Unencumbered", "Burdened",
            "Stressed", "Strained", "Overtaxed" or "Overloaded" """
        statLine = self.screen.getRow (23, start=50)
        for stat in ["Burdened", "Stressed", "Strained", "Overtaxed", "Overloaded"]:
            if stat in statLine:
                return stat
        return "Unemcumbered"
