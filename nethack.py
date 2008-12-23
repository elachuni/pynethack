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

import pexpect
from scraper import Screen
import nethackkeys as keys
import time
import sys
import os
from interactions import checkPendingInteraction, YesNoInteraction, YesNoQuitInteraction, SelectInteraction, SelectDialogInteraction, DirectionInteraction, CursorPointInteraction, FreeEntryInteraction, Information
from items import Item, Spell

class NetHackPlayer(object):
    initialRole = "Random"
    initialRace = "Random"
    initialGender = "Random"
    initialAlignment = "Random"
    def __init__(self, user=None, passwd=None, host=None):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.pendingInteraction = None
        self.info = None
        self.history = []
        self.echo = False
        os.environ['LINES'] = '24'
        os.environ['COLUMNS'] = '80'
        os.environ['TERM'] = 'xterm'
        if host is None:
            userstr = (not user is None) and ('-u ' + user) or ''
            self.child = pexpect.spawn ("nethack %s" % userstr)
        else:
            self.child = pexpect.spawn ("telnet %s" % host)
        self.screen = Screen()
        if not self.host is None:
            self.login()

    def __getstate__(self):
        state = dict(self.__dict__)
        del state['child']
        return state

    def __setstate__(self, state):
        """ FIXME: __setstate__ duplicates constructor functionallity """
        os.environ['LINES'] = '24'
        os.environ['COLUMNS'] = '80'
        os.environ['TERM'] = 'xterm'
        self.__dict__ = state
        if self.host is None:
            userstr = (not self.user is None) and ('-u ' + self.user) or ''
            self.child = pexpect.spawn ("nethack %s" % userstr)
        else:
            self.child = pexpect.spawn ("telnet %s" % self.host)

    def send (self, msg):
        """ Sends 'msg' down the wire. """
        checkPendingInteraction(self)
        self.child.send (msg)

    def sendline (self, msg):
        """ Sends 'msg' down the wire followed by a newline character. """
        checkPendingInteraction(self)
        self.child.sendline (msg)

    def login(self):
        """ Enter user/password credentials.
            This is only needed when running against a remotely hosted server. """
        self.watch ("=> ") # Welcome screen
        opts = self.parseOptions (") ", 1, self.screen.cursorY - 6, 40, 4)
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
        self.watch ("=> ")
        opts = self.parseOptions (") ", 1, 13, 40, 6)
        if opts.has_key ("play nethack!"):
            self.send (opts['play nethack!']) # attempt to launch a new game

    def play(self):
        """ Start a new game and select role, race, gender and alignment """
        checkPendingInteraction(self)
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
        if isinstance(expecting, basestring):
            expecting = [expecting]
        patterns = ['--More--', pexpect.TIMEOUT, pexpect.EOF]
        matched = None
        found = False
        info = []
        self.info = None
        while not found:
            i = self.child.expect (patterns, timeout=0.3)
            self.screen.printstr(self.child.before)
            if not self.child.after in [pexpect.TIMEOUT, pexpect.EOF]:
                self.screen.printstr(self.child.after)
            if i == 0:
                # --More--
                if self.screen.cursorY == 0:
                    msg = [self.screen.getRow(0, start=0, finish=self.screen.cursorX - 9).strip()]
                elif self.screen.cursorY == 1:
                    msg = [self.screen.getRow(0) +
                           self.screen.getRow(1, start=0, finish=self.screen.cursorX - 9).strip()]
                else:
                    msg = self.screen.getArea(self.screen.cursorX - 9, 0, 80, self.screen.cursorY)
                info += msg
                self.send (' ')
            elif i == 1:
                # Timed out.
                #  First: attempt to match what the user is expecting.
                if not expecting is None:
                    matched = self.screen.multiMatch(expecting)
                    if not matched is None:
                        found = True
                if not found:
                    if self.screen.matches (r'.* \[yn\]( \(.\))? ?'):
                        matched = YesNoInteraction (self, self.screen.lastMatch())
                        found = True
                    elif self.screen.matches (r'.* \[ynq\]( \(.\))? ?'):
                        matched = YesNoQuitInteraction (self, self.screen.lastMatch())
                        found = True
                    elif self.screen.matches (r'.* \[.* or \?\*\] '):
                        matched = SelectInteraction (self, self.screen.lastMatch())
                        found = True
                    elif self.screen.matches (r'\(end\) |\(\d of\d\) '):
                        matched = SelectDialogInteraction (self, question=selectDialogQuestion)
                        found = True
                    elif self.screen.matches (r'In what direction.*\?.*'):
                        matched = DirectionInteraction (self, self.screen.lastMatch())
                        found = True
                    elif self.screen.cursorY == 0:
                        # This can't be waiting for the player to move, we guess it's a free entry question
                        matched = FreeEntryInteraction (self, self.screen.getRow(0).strip())
                        found = True
                    #elif... select position with cursor interaction
                    #  Finally, assume the next turn is ready, and hand over control
                    else:
                        msg = self.screen.getRow(0).strip()
                        if len(msg) > 0:
                            info += [msg]
                        found = True
                #if matched is None:
                    #print "Expecting", expecting
                    #print "Found '%s'" % self.screen.getRow (
                     #self.screen.cursorY, 0,
                     #self.screen.cursorX)
                    #print "Timed out with an unexpected output :-("
                    #print "Cursor at %d,%d" % (self.screen.cursorY, self.screen.cursorX)
                    #print "Output so far:", [self.child.before]
                    #print "Expecting:", patterns
                    #print "Happy hacking!"
                    #raise ValueError, "Unexpected Output"
            elif i == 2:
                # Game finished
                found = True
            if self.echo:
                self.screen.dump()
        if len(info) > 0:
            self.info = Information (self, info)
            self.history.append(self.info)
            if matched is None:
                matched = self.info
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

    def quaff (self, potion=Item('*')):
        """ Quaff a potion.
            'potion' should have been retrieved from our inventory recently.
            If you leave 'potion' as default, a SelectDialogInteraction will return"""
        self.send ('q')
        matched = self.watch()
        if isinstance (matched, SelectInteraction):
            matched = matched.answer (potion)
        return matched

    def eat (self, food=Item('*')):
        """ Eat something.
            'food' should have been retrieved from our inventory recently.
            If you leave 'potion' as default, a SelectDialogInteraction will return """
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

    def takeOff (self, item=Item('*')):
        """ Take off a garment.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        self.send ('T')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'take off' in matched.question:
            matched = matched.answer (item)
        return matched

    def quiver (self, item=Item('*')):
        """ Ready an item in your quiver to be able to fire it using the 'fire' method.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        self.send ('Q')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'ready' in matched.question:
            matched = matched.answer (item)
        return matched

    def wear (self, item=Item('*')):
        """ Put on a piece of clothing.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
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

    def apply(self, item=Item('*')):
        """ Use or apply an item.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        self.send ('a')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'use or apply' in matched.question:
            matched = matched.answer (item)
        return matched

    def remove (self, item=Item('*')):
        """ Remove an accessory.
            If no 'item' is passed in, a SelectDialogInteraction is returned. """
        self.send ('R')
        matched = self.watch()
        if isinstance (matched, SelectInteraction) and 'remove' in matched.question:
            matched = matched.answer (item)
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
            matched = CursorPointInteraction (self, matched.message)
            matched = matched.answer (x, y)
        return matched

    def travel (self, x, y):
        """ Move via a shortest-path algorithm to a point on the map """
        self.send ("_")
        matched = self.watch ()
        if isinstance (matched, Information) and '(For instructions type a ?)' in matched.message[0]:
            matched = CursorPointInteraction (self, matched.message)
            matched = matched.answer (x, y)
        return matched

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
            lines = self.screen.getArea (self.screen.cursorX - len(matched), 0, h=self.screen.cursorY)
            for line in lines:
                if line.find(' - ') == -1:
                    category = line.strip()
                else:
                    key, item = line.split(' - ', 1)
                    it = Item (key.strip(), description=item.strip(), category=category)
                    inventory.append(it)
            self.send (' ')
            if matched != '(1 of 2)':
                more_pages = False
        self.watch()
        if isinstance (categories, basestring):
            categories = [categories]
        if categories is None:
            return inventory
        else:
            return [item for item in inventory if item.category in categories]

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
        val = statLine.find ('Exp:') + 4
        return int(statLine[val : statLine.find ('/', val + 1)])

    def experience (self):
        """ Returns my current experience as an int. Compare with 'experienceLevel' """
        statLine = self.screen.getRow (23)
        val = statLine.find ('Xp:')
        if val > -1:
            val = statLine.find ('/', val + 3) + 1
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

    def x(self):
        """ Returns our current x-position (column) within the current dungeon level """
        checkPendingInteraction (self)
        return self.screen.cursorX

    def y(self):
        """ Returns our current y-position (row) within the current dungeon level """
        checkPendingInteraction (self)
        return self.screen.cursorY - 1 # There's one row of heading above the maze

    def look(self, x, y):
        checkPendingInteraction (self)
        if 0 > x or x >= 80 or 0 > y or y >= 21:
            raise ValueError, "Invalid cell position (%d,%d)" % (x, y)
        return self.screen.screen[y + 1][x]

    def interact(self):
        """ Play for yourself for a while """
        checkPendingInteraction(self)
        self.child.send (chr(18)) # CTRL+R to redraw screen
        self.child.interact (escape_character=chr(1))
        print "\n"*25
        self.child.send (chr(18))
        return self.watch()
