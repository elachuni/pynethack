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

class NetHackPlayer(object):
    def __init__(self):
        self.child = pexpect.spawn ("telnet localhost")
        self.screen = Screen()

    def login(self):
        self.watch ("=> ") # Welcome screen
        opts = self.parseOptions (") ", 1, 13, 40, 4)
        if opts.has_key ("login"):
            self.child.send (opts['login']) # attempt log in
        else:
            raise ValueError, "login called, but we're not at the welcome screen"
        self.watch ("=> ")
        self.child.sendline (self.user)
        self.watch ("=> ")
        if self.screen.getRow (9).strip() == 'There was a problem with your last entry.':
            raise ValueError, "invalid username"
        self.child.sendline (self.passwd)

    def new_game(self):
        self.watch ("=> ") # We should already be logged in
        opts = self.parseOptions (") ", 1, 13, 40, 6)
        if opts.has_key ("play nethack!"):
            self.child.send (opts['play nethack!']) # attempt log in
        else:
            raise ValueError, "new_game called, but we're not at the main menu"
        match = self.watch (['[ynq] ', ' 10'])
        if match == '[ynq] ':
            self.child.send ('n')
        elif match == ' 10':
            print "Waiting 10 seconds for old save game to be restored...\n"
            # Wait 10 seconds for old game to be restored
            time.sleep(10)
        self.watch ('(end) ')
        if self.screen.getRow(0).find('Role') >= 0:
            self.child.send(keys.roles[self.role])
            self.watch ('(end) ')
        if self.screen.getRow(0).find('Race') >= 0:
            self.child.send(keys.races[self.race])
            self.watch ('(end) ')
        if self.screen.getRow(0).find('Gender') >= 0:
            self.child.send(keys.genders[self.gender])
            self.watch ('(end) ')
        if self.screen.getRow(0).find('Alignment') >= 0:
            self.child.send(keys.alignments[self.alignment])
            self.watch()

    def watch (self, expecting=None, new_turn = True):
        if new_turn:
            self.info = []
            self.cachedInventory = None
        if type(expecting) == type(''):
            expecting = [expecting]
        patterns = ['--More--', pexpect.TIMEOUT]
        matched = None
        should_print = False
        while matched is None:
            i = self.child.expect (patterns, timeout=0.5)
            self.screen.printstr(self.child.before)
            if self.child.after != pexpect.TIMEOUT:
                self.screen.printstr(self.child.after)
            if i == 0:
                # --More--
                self.info += self.screen.getArea(self.screen.cursorX - 9, 0, 80, self.screen.cursorY)
                self.child.send (' ')
                should_print = True
            elif i == 1:
                # Timed out
                if self.screen.getCharAtRelativePos() == '@':
                    msg = self.screen.getRow(0).strip()
                    if len(msg) > 0:
                        self.info += [msg]
                    matched = '@'
                    should_print = True
                elif self.screen.getRow (0)[:40] == 'Do you want your possessions identified?':
                    # You're dead... hand over control
                    self.child.interact()
                    sys.exit()
                elif not expecting is None:
                    for prompt in expecting:
                        if self.screen.getRow (self.screen.cursorY, self.screen.cursorX - len(prompt),
                           self.screen.cursorX) == prompt:
                            # Arrived at the expected prompt
                            matched = prompt
                            should_print = True
                if matched is None:
                    print "Expecting", expecting
                    print "Found '%s'" % self.screen.getRow (
                     self.screen.cursorY, 0,
                     self.screen.cursorX)
                    print "Timed out with an unexpected output :-("
                    self.screen.dump()
                    print "Cursor at %d,%d" % (self.screen.cursorY, self.screen.cursorX)
                    print "Output so far:", [self.child.before]
                    print "Expecting:", patterns
                    print "Happy hacking!"
                    sys.exit(-1)
            if should_print:
                self.screen.dump()
                time.sleep(2)
        sys.stdout.flush()
        return matched

    def parseOptions (self, sep, x, y, w, h):
        lines = self.screen.getArea (x, y, w, h)
        splits = [line.split(sep) for line in lines]
        strips = [(opt[1].strip().lower(), opt[0].strip()) for opt in splits if len(opt) == 2]
        return dict(strips)

    def run (self):
        self.child.interact()

    def go (self, direction):
        print "Going %s..." % direction
        self.child.send (keys.go[direction])
        self.watch()

    def quaff (self, potion):
        print "Quaffing %s..." % potion['description']
        self.child.send ('q')
        self.watch('] ', new_turn=False)
        self.child.send (potion['key'])
        self.watch()

    def eat (self, food):
        print "Eating %s..." % food['description']
        self.child.send ('e')
        self.watch('] ', new_turn=False)
        self.child.send (food['key'])
        ev = self.watch('Stop eating? [yn] (y) ')
        if ev == 'Stop eating? [yn] (y) ':
            self.child.send ('y')
            self.watch()

    def sit (self):
        print "Sitting"
        self.child.sendline ("#sit")
        self.watch(new_turn=False)

    def inventory (self, categories=None):
        if self.cachedInventory is None:
            self.child.send ('i')
            more_pages = True
            self.cachedInventory = []
            while more_pages:
                matched = self.watch(['(end) ', '(1 of 2)', '(2 of 2)'], new_turn=False)
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
                self.child.send (' ')
                if matched != '(1 of 2)':
                    more_pages = False
            self.watch(new_turn=False)
        print "Self cachedInventory:", self.cachedInventory
        if categories is None:
            return self.cachedInventory
        else:
            return [item for item in self.cachedInventory if item['category'] in categories]

    def myStr (self):
        """Returns my current strength.  For strength above 18 a floating point number is returned,
           as in 18/25 -> 18.25.  For 18/** return 19."""
        attsLine = self.screen.getRow(22, start=23)
        st = attsLine.find('St:') + 3
        if attsLine[st:st+5] == '18/**': # Special case this one out
            return 19
        else:
            return float(attsLine[st : attsLine.find(' ', st + 1)].replace('/', '.'))

    def myDex (self):
        attsLine = self.screen.getRow(22, start=23)
        dx = attsLine.find('Dx:') + 3
        return int(attsLine[dx : attsLine.find (' ', dx + 1)])

    def myCon (self):
        attsLine = self.screen.getRow(22, start=23)
        co = attsLine.find('Co:') + 3
        return int(attsLine[co : attsLine.find (' ', co + 1)])

    def myInt (self):
        attsLine = self.screen.getRow(22, start=23)
        val = attsLine.find('In:') + 3
        return int(attsLine[val : attsLine.find (' ', val + 1)])

    def myWis (self):
        attsLine = self.screen.getRow(22, start=23)
        wi = attsLine.find('Wi:') + 3
        return int(attsLine[wi : attsLine.find (' ', wi + 1)])

    def myCha (self):
        attsLine = self.screen.getRow(22, start=23)
        ch = attsLine.find('Ch:') + 3
        return int(attsLine[ch : attsLine.find (' ', ch + 1)])

