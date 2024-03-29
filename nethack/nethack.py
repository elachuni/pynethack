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

# Run against a local nethack game
# or against a DGameLaunch server (ftp://ftp.alt.org/pub/dgamelaunch/)

import nethackkeys as keys
import time

from interactions import checkPendingInteraction, YesNoInteraction, \
     YesNoQuitInteraction, SelectInteraction, SelectDialogInteraction, \
     DirectionInteraction, CursorPointInteraction, FreeEntryInteraction, \
     Information

from items import Item, Spell

class NetHackPlayer(object):
    initialRole = "Random"
    initialRace = "Random"
    initialGender = "Random"
    initialAlignment = "Random"
    def __init__(self, server):
        self.server = server

    def send (self, msg):
        """ Sends 'msg' down the wire. """
        checkPendingInteraction(self.server)
        self.server.send (msg)

    def sendline (self, msg):
        """ Sends 'msg' down the wire followed by a newline character. """
        checkPendingInteraction(self.server)
        self.server.sendline (msg)

    def play(self):
        """ Start a new game and select role, race, gender and alignment """
        checkPendingInteraction(self.server)
        match = self.watch (r'in 1')
        if match == 'in 1':
            print "Waiting 10 seconds for old save game to be restored...\n"
            # Wait 10 seconds for old game to be restored
            time.sleep(11)
        elif isinstance (match, YesNoQuitInteraction):
            match = match.answer ('n')
        elif isinstance (match, YesNoInteraction) and match.question == 'There is already a game in progress under your name.  Destroy old game?':
            return match
        if isinstance (match, SelectDialogInteraction) and 'Role' in match.question:
            match = match.answer (Item(keys.roles[self.initialRole]))
        if isinstance (match, SelectDialogInteraction) and 'Race' in match.question:
            match = match.answer (Item(keys.races[self.initialRace]))
        if isinstance (match, SelectDialogInteraction) and 'Gender' in match.question:
            match = match.answer (Item(keys.genders[self.initialGender]))
        if isinstance (match, SelectDialogInteraction) and 'Alignment' in match.question:
            match = match.answer (Item(keys.alignments[self.initialAlignment]))
        return match

    def watch (self, expecting=None, selectDialogQuestion=None):
        """ Update the screen and see what happens.
            'expecting' is a regex or list of regexes that are checked before regular interactions.
            'selectDialogQuestion' is a question for selectDialogs, that often show the question before
                                   the dialog. """
        return self.server.watch(expecting, selectDialogQuestion)

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
        self.send (keys.dirs[direction])
        return self.watch()

    def open (self, direction):
        """ Open a door in the specified direction.  See 'go' for list of possible directions. """
        self.send ('o')
        matched = self.watch()
        if isinstance (matched, DirectionInteraction):
            matched = matched.answer (direction)
        return matched

    def close (self, direction):
        """ Close a door in the specified direction.  See 'go' for list of possible directions. """
        self.send ('c')
        matched = self.watch()
        if isinstance (matched, DirectionInteraction):
            matched = matched.answer (direction)
        return matched

    def kick (self, direction):
        """ Kick in the specified direction.  See 'go' for a list of possible directions. """
        self.send ('\x04')
        matched = self.watch()
        if isinstance (matched, DirectionInteraction):
            matched = matched.answer (direction)
        return matched

    def fight (self, direction):
        """ Fight (even if you don't sense a monster) in the specified direction. """
        self.send ('F')
        self.send (keys.dirs[direction])
        return self.watch()

    def quaff (self, potion=None):
        """ Quaff a potion.
            'potion' should have been retrieved from our inventory recently.
            If you leave 'potion' as default, a SelectDialogInteraction will return"""
        if not isinstance(potion, Item):
            raise ValueError ('Expected an Item')
        self.send ('q')
        matched = self.watch()
        if isinstance (matched, SelectInteraction):
            matched = matched.answer (potion)
        return matched

    def eat (self, food=None):
        """ Eat something.
            'food' should have been retrieved from our inventory recently.
            If you leave 'potion' as default, a SelectDialogInteraction will return """
        if food is None:
            food = Item('*')
        if not isinstance(food, Item):
            raise ValueError ('Expected an Item')
        self.send ('e')
        matched = self.watch()
        if isinstance (matched, SelectInteraction):
            matched = matched.answer (food)
        return matched

    def offer (self, corpse=Item('*')):
        """ Offer a sacrifice to the gods. """
        self.sendline ('#offer')
        matched = self.watch()
        if isinstance (matched, SelectInteraction):
            matched = matched.answer (corpse)
        return matched

    def rub (self, item=Item('*')):
        """ Rub a lamp or a stone """
        self.sendline ('#rub')
        matched = self.watch()
        if isinstance (matched, SelectInteraction):
            matched = matched.answer (item)
        return matched

    def sit (self):
        """ Sit down """
        self.sendline ("#sit")
        return self.watch()

    def rest (self):
        """ Wait a moment """
        self.send (".")
        return self.watch()

    def exchange (self):
        """ Exchange primary and secondary weapons """
        self.send ("x")
        return self.watch()

    def pray (self):
        """ Pray to the gods for help"""
        self.sendline ("#pray")
        matched = self.watch()
        if isinstance (matched, YesNoInteraction) and 'Are you sure' in matched.question:
            matched = matched.answer ('yes')
            matched = self.watch()
        return matched

    def search (self):
        """ Search around for hidden stuff"""
        self.send ('s')
        return self.watch()

    def fire (self, direction):
        """ Fire your readied ammunition in a certain direction.
            If no ammunition is readied, a SelectDialog will be returned."""
        self.send ('f')
        matched = self.watch()
        if isinstance (matched, DirectionInteraction):
            matched = matched.answer (direction)
        return matched

    def drop (self, item=Item('*'), amount=None):
        """ Drop an item.  'item' should have been retrieved recently from our inventory.
            If 'amount' is an integer, drop that amount of items
            (to drop one gold piece, for example) """
        self.send ('d')
        if not amount is None:
            self.send (str(amount))
        matched = self.watch()
        if isinstance (matched, SelectInteraction):
            matched = matched.answer (item)
        return matched

    def multiDrop (self, items):
        """ Drop multiple items. 'items' is a list of stuff from our inventory. """
        self.send ('D')
        matched = self.watch()
        if isinstance (matched, SelectDialogInteraction) and 'what type' in matched.question:
            matched = matched.answer ([Item('a')]) # All types
        if isinstance (matched, SelectDialogInteraction) and 'What would you like to drop' in matched.question:
            matched = matched.answer (items)
        return matched

    def pickUp (self):
        """ Pick one or more items up off the ground."""
        self.send (',')
        return self.watch ()

    def takeOff (self, item=None):
        """ Take off a garment.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        if item is None:
            item = Item('*')
        if not isinstance(item, Item):
            raise ValueError ('Expected an Item')
        self.send ('T')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'take off' in matched.question:
            matched = matched.answer (item)
        return matched

    def quiver (self, item=None):
        """ Ready an item in your quiver to be able to fire it using the 'fire' method.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        if item is None:
            item = Item('*')
        if not isinstance(item, Item):
            raise ValueError ('Expected an Item')
        self.send ('Q')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'ready' in matched.question:
            matched = matched.answer (item)
        return matched

    def wear (self, item=None):
        """ Put on a piece of clothing.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        if item is None:
            item = Item('*')
        if not isinstance(item, Item):
            raise ValueError ('Expected an Item')
        self.send ('W')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'wear' in matched.question:
            matched = matched.answer (item)
        return matched

    def putOn (self, item=Item('*')):
        """ Put on an accessory.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        self.send ('W')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'put on' in matched.question:
            matched = matched.answer (item)
        return matched

    def wield (self, item=Item('*')):
        """ Wield a weapon.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        self.send ('w')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'wield' in matched.question:
            matched = matched.answer (item)
        return matched

    def read (self, item=Item('*')):
        """ Read a book or scroll.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        self.send ('r')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'read' in matched.question:
            matched = matched.answer (item)
        return matched

    def throw(self, item=Item('*'), direction=None):
        """ Throw an item.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        self.send ('t')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'throw' in matched.question:
            matched = matched.answer (item)
        if isinstance (matched, DirectionInteraction) and not direction is None:
            matched = matched.answer (direction)
        return matched

    def name (self, item=Item('*'), individualObject=True, name=None):
        """ Name an individual object """
        self.sendline ('#name')
        matched = self.watch()
        if isinstance (matched, YesNoQuitInteraction) and 'Name an individual object' in matched.question:
            answer = individualObject and 'y' or 'n'
            matched = matched.answer (answer)
        if isinstance (matched, SelectInteraction) and 'name' in matched.question:
            matched = matched.answer (item)
        if isinstance (matched, FreeEntryInteraction) and 'What do you want to name' in matched.question:
            if name is not None:
                matched = matched.answer (name)
        return matched

    def call (self, x, y, name=None):
        """ Name an individual monster (ex. baptize your dog) """
        self.send ('C')
        matched = self.watch ()
        if isinstance (matched, Information) and matched.message == ['(For instructions type a ?)']:
            matched = CursorPointInteraction (self, matched.message)
            matched = matched.answer (x, y)
        if isinstance (matched, FreeEntryInteraction) and 'What do you want to call' in matched.question:
            if name is not None:
                matched = matched.answer (name)
        return matched

    def engrave (self, using, msg=None):
        """ Write a message in the dust on the floor (if using=Item('-') use fingers) """
        self.send ('E')
        matched = self.watch ()
        if isinstance (matched, SelectInteraction) and 'write with' in matched.question:
            matched = matched.answer (using)
        if isinstance (matched, FreeEntryInteraction) and 'What do you want to write' in matched.question:
            if msg is not None:
                matched = matched.answer (msg)
        return matched

    def apply(self, item=None):
        """ Use or apply an item.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        if item is None:
            item = Item('*')
        self.send ('a')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'use or apply' in matched.question:
            matched = matched.answer (item)
        return matched

    def remove (self, item=None):
        """ Remove an accessory.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        if item is None:
            item = Item('*')
        self.send ('R')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'remove' in matched.question:
            matched = matched.answer (item)
        return matched

    def loot (self, takeOut=True):
        """ Loot a box or container.
            By default we'll try to take stuff out of the box.  To put stuff
                into the box, set takeOut=False
            At this moment you can't do both (take out and put in) at the same
                time, you'll need to call loot() twice to do that.
            Returns a SelectDialogInteraction if everything goes ok. """
        self.sendline ('#loot')
        matched = self.watch()
        if isinstance (matched, YesNoQuitInteraction) and 'loot it' in matched.question:
            matched = matched.answer ('y')
        if isinstance (matched, SelectDialogInteraction) and 'Do what?' in matched.question:
            if takeOut:
                answer = 'Take something out'
            else:
                answer = 'Put something in'
            for ans in matched.options:
                if answer in ans.description:
                    matched = matched.answer(ans)
                    break
            else:
                matched = matched.answerDefault()
            if isinstance(matched, SelectDialogInteraction) and 'what type of objects?' in matched.question:
                matched = matched.answer([matched.options[0]]) # All types
        return matched

    def zap (self, item=Item('*')):
        """ Zap a wand.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        self.send ('z')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'zap' in matched.question:
            matched = matched.answer (item)
        return matched

    def cast (self, spell=None):
        """ Cast a spell.
            If no 'spell' is passed in, a SelectDialogInteraction is returned. """
        self.send ('Z')
        matched = self.watch()
        if isinstance (matched, SelectDialogInteraction) and not spell is None:
            matched = matched.answer (spell)
        return matched

    def describe (self, x, y):
        """ Look at what is at a certain coordinate in the dungeon """
        self.send (";")
        matched = self.watch ()
        if isinstance (matched, Information) and matched.message == ['Pick an object.']:
            matched = CursorPointInteraction (self.server, matched.message)
            matched = matched.answer (x, y)
        return matched

    def travel (self, x, y):
        """ Move via a shortest-path algorithm to a point on the map """
        self.send ("_")
        matched = self.watch ()
        if isinstance (matched, Information) and '(For instructions type a ?)' in matched.message[0]:
            matched = CursorPointInteraction (self.server, matched.message)
            matched = matched.answer (x, y)
        return matched

    def look(self, x, y):
        """ Look at what's currently visible at position (x,y) in the maze """
        checkPendingInteraction (self.server)
        if 0 > x or x >= 80 or 0 > y or y >= 21:
            raise ValueError, "Invalid cell position (%d,%d)" % (x, y)
        return self.server.cellAt(x, y + 1)

    def save(self):
        """ Save this game and exit """
        self.send ('S')
        matched = self.watch ()
        if isinstance (matched, YesNoInteraction):
            matched = matched.answer('y')
        return matched

    def quit (self):
        """ Abandon this game """
        self.sendline ('#quit')
        matched = self.watch ()
        if isinstance (matched, YesNoInteraction):
            matched = matched.answer ('y')
        return matched

    def inventory (self, categories=None):
        """ Retrieve your inventory.  'categories' can be a list of strings describing the categories
            you want to restrict to, as "Weapons", "Potions", etc. """
        self.send ('i')
        more_pages = True
        inventory = []
        while more_pages:
            matched = self.watch([r'\(end\) ', r'\(\d of \d\)'])
            lines = self.server.getArea (self.server.cursorX() - len(matched.group(0)), 0, h=self.server.cursorY())
            for line in lines:
                if line.find(' - ') == -1:
                    category = line.strip()
                else:
                    key, item = line.split(' - ', 1)
                    it = Item (key.strip(), description=item.strip(), category=category)
                    inventory.append(it)
            self.send (' ')
            if matched.group(0) != '(1 of 2)':
                more_pages = False
        self.watch()
        if isinstance (categories, basestring):
            categories = [categories]
        if categories is None:
            return dict((item.key, item) for item in inventory)
        else:
            return dict((item.key, item) for item in inventory if item.category in categories)

    def strength (self):
        """Returns my current strength.  For strength above 18 a floating point number is returned,
           as in 18/25 -> 18.25.  For 18/** return 19."""
        statLine = self.server.getRow(22, start=23)
        st = statLine.find('St:') + 3
        if statLine[st:st+5] == '18/**': # Special case this one out
            return 19.0
        else:
            return float(statLine[st : statLine.find(' ', st + 1)].replace('/', '.'))

    def dexterity (self):
        """ Returns my current dexterity as an int """
        statLine = self.server.getRow(22, start=23)
        dx = statLine.find('Dx:') + 3
        return int(statLine[dx : statLine.find (' ', dx + 1)])

    def constitution (self):
        """ Returns my current constitution as an int """
        statLine = self.server.getRow (22, start=23)
        co = statLine.find('Co:') + 3
        return int(statLine[co : statLine.find (' ', co + 1)])

    def intelligence (self):
        """ Returns my current intelligence as an int """
        statLine = self.server.getRow (22, start=23)
        val = statLine.find('In:') + 3
        return int(statLine[val : statLine.find (' ', val + 1)])

    def wisdom (self):
        """ Returns my current wisdom as an int """
        statLine = self.server.getRow (22, start=23)
        wi = statLine.find('Wi:') + 3
        return int(statLine[wi : statLine.find (' ', wi + 1)])

    def charisma (self):
        """ Returns my current charisma as an int """
        statLine = self.server.getRow (22, start=23)
        ch = statLine.find('Ch:') + 3
        return int(statLine[ch : statLine.find (' ', ch + 1)])

    def alignment (self):
        """ Returns my current alignment as a string: one of "Lawful", "Chaotic" or "Neutral" """
        statLine = self.server.getRow (22, start=60)
        for align in keys.alignments.keys():
            if align in statLine:
                return align

    def hitPoints (self):
        """ Returns my current hit-points as an int """
        statLine = self.server.getRow (23)
        hp = statLine.find ('HP:') + 3
        return int(statLine[hp : statLine.find ('(', hp + 1)])

    def maxHitPoints (self):
        """ Returns my current maximum hit-points as an int """
        statLine = self.server.getRow (23)
        hp = statLine.find ('HP:') + 3
        hp = statLine.find ('(', hp) + 1
        return int(statLine[hp : statLine.find (')', hp + 1)])

    def gold (self):
        """ Returns the amount of gold in my purse, as an int """
        statLine = self.server.getRow (23)
        val = statLine.find ('$:') + 2
        return int(statLine[val : statLine.find (' ', val + 1)])

    def dungeonLevel (self):
        """ Returns my current dungeon level as an int """
        statLine = self.server.getRow (23)
        val = statLine.find ('Dlvl:') + 5
        return int(statLine[val : statLine.find (' ', val + 1)])

    def power (self):
        """ Returns my current power as an int """
        statLine = self.server.getRow (23)
        val = statLine.find ('Pw:') + 3
        return int(statLine[val : statLine.find ('(', val + 1)])

    def maxPower (self):
        """ Returns my current maximum power as an int """
        statLine = self.server.getRow (23)
        val = statLine.find ('Pw:') + 3
        val = statLine.find ('(', val) + 1
        return int(statLine[val : statLine.find (')', val + 1)])

    def armourClass (self):
        """ Returns my current armour class as an int """
        statLine = self.server.getRow (23)
        val = statLine.find ('AC:') + 3
        return int(statLine[val : statLine.find (' ', val + 1)])

    def experienceLevel (self):
        """ Returns my current experience level as an int.  Compare with 'experience' """
        statLine = self.server.getRow (23)
        val = statLine.find ('Exp:') + 4
        return int(statLine[val : statLine.find ('/', val + 1)])

    def experience (self):
        """ Returns my current experience as an int. Compare with 'experienceLevel' """
        statLine = self.server.getRow (23)
        val = statLine.find ('Xp:')
        if val > -1:
            val = statLine.find ('/', val + 3) + 1
            return int(statLine[val : statLine.find (' ', val + 1)])

    def turn (self):
        """ Returns the contents of the turn counter as an int """
        statLine = self.server.getRow (23)
        val = statLine.find ('T:') + 2
        if val == 1: # find returned -1
            return -1
        return int(statLine[val : statLine.find (' ', val + 1)])

    def hungerStatus (self):
        """ Returns my current hunger status as a string: one of "Satiated", "Not Hungry",
            "Hungry", "Weak", or "Fainting" """
        statLine = self.server.getRow (23, start=40)
        for stat in ["Satitated", "Hungry", "Weak", "Fainting"]:
            if stat in statLine:
                return stat
        return "Not Hungry"

    def confused (self):
        """ Returns True if I'm currently confused """
        statLine = self.server.getRow (23, start=50)
        return "Conf" in statLine

    def stunned (self):
        """ Returns True if I'm currently stunned """
        statLine = self.server.getRow (23, start=50)
        return "Stun" in statLine

    def foodPoisoned (self):
        """ Returns True if I'm currently food poisoned """
        statLine = self.server.getRow (23, start=50)
        return "FoodPois" in statLine

    def ill (self):
        """ Returns True if I'm currently ill """
        statLine = self.server.getRow (23, start=50)
        return "Ill" in statLine

    def blind (self):
        """ Returns True if I'm currently blind """
        statLine = self.server.getRow (23, start=50)
        return "Blind" in statLine

    def hallucinating (self):
        """ Returns True if I'm currently hallucinating """
        statLine = self.server.getRow (23, start=50)
        return "Hallu" in statLine

    def slimed (self):
        """ Returns True if I'm currently turning in to a slime """
        statLine = self.server.getRow (23, start=50)
        return "Slime" in statLine

    def encumbrance (self):
        """ Returns my current encumbrance status as a string: one of "Unencumbered", "Burdened",
            "Stressed", "Strained", "Overtaxed" or "Overloaded" """
        statLine = self.server.getRow (23, start=40)
        for stat in ["Burdened", "Stressed", "Strained", "Overtaxed", "Overloaded"]:
            if stat in statLine:
                return stat
        return "Unencumbered"

    def x(self):
        """ Returns our current x-position (column) within the current dungeon level """
        checkPendingInteraction (self.server)
        return self.server.cursorX()

    def y(self):
        """ Returns our current y-position (row) within the current dungeon level """
        checkPendingInteraction (self.server)
        return self.server.cursorY() - 1 # There's one row of heading above the maze

    def interact(self):
        """ Play for yourself for a while """
        checkPendingInteraction(self.server)
        self.server.interact()
        return self.watch()

