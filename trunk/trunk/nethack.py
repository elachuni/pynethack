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
        self.watch ('[ynq] ')
        self.child.send ('n')
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

    def watch (self, expecting=None):
        self.info = []
        patterns = ['--More--', pexpect.TIMEOUT]
        found = False
        should_print = False
        while not found:
            i = self.child.expect (patterns, timeout=4)
            self.screen.printstr(self.child.before)
            if self.child.after != pexpect.TIMEOUT:
                self.screen.printstr(self.child.after)
            if i == 0:
                self.info += self.screen.getArea(self.screen.cursorX - 9, 0, 80, self.screen.cursorY)
                self.child.send (' ')
                should_print = True
            elif i == 1:
                # Timed out
                if self.screen.getCharAtRelativePos() == '@':
                    # Next turn
                    msg = self.screen.getRow(0).strip()
                    if len(msg) > 0:
                        self.info += [msg]
                    found = True
                    should_print = True
                elif (not expecting is None) and (self.screen.getRow (
                  self.screen.cursorY, self.screen.cursorX - len(expecting),
                  self.screen.cursorX) == expecting):
                    # Arrived at the expected prompt
                    found = True
                    should_print = True
                elif self.screen.getRow (0)[:40] == 'Do you want your possessions identified?':
                    # You're dead... hand over control
                    self.child.interact()
                else:
                    print "Expecting", expecting
                    print "Found '%s'" % (self.screen.getRow (
                     self.screen.cursorY, self.screen.cursorX - len(expecting),
                     self.screen.cursorX),)
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

class VeryDumbPlayer (NetHackPlayer):
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

if __name__ == '__main__':
    a = VeryDumbPlayer()
    a.login()
    a.new_game()
    a.run()
