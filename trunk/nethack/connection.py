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

# The main class defined in this file is NetHackConnection.  This class
# abstracts a connection to the game (local or remote).

import pexpect
from scraper import Screen, WIDTH, HEIGHT
import os
from interactions import YesNoInteraction, YesNoQuitInteraction, SelectInteraction, SelectDialogInteraction, DirectionInteraction, FreeEntryInteraction, Information

class NetHackConnection(object):
    """ Base class for Nethack connections.  Instantiating this class won't
        work, as we count on having a 'child' attribute.  Descendants should
        set this appropriately. """
    def __init__(self, screen=None):
        self.echo = False
        if screen is None:
            screen = Screen()
        self.screen = screen
        self.info = None
        self.history = []
        self.child = None # The actual connection
        self.patchEnvironment()

    def patchEnvironment(self):
        os.environ['LINES'] = '24'
        os.environ['COLUMNS'] = '80'
        os.environ['TERM'] = 'xterm'

    def __getstate__(self):
        state = dict(self.__dict__)
        del state['child']
        return state

    def send (self, msg):
        """ Sends 'msg' down the wire. """
        self.child.send (msg)

    def sendline (self, msg):
        """ Sends 'msg' down the wire followed by a newline character. """
        self.child.sendline (msg)

    def watch (self, player, expecting=None, selectDialogQuestion=None):
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
                        matched = YesNoInteraction (player, self.screen.lastMatch())
                        found = True
                    elif self.screen.matches (r'.* \[ynq\]( \(.\))? ?'):
                        matched = YesNoQuitInteraction (player, self.screen.lastMatch())
                        found = True
                    elif self.screen.matches (r'.* \[.* or \?\*\] '):
                        matched = SelectInteraction (player, self.screen.lastMatch())
                        found = True
                    elif self.screen.matches (r'\(end\) |\(\d of\d\) '):
                        matched = SelectDialogInteraction (self, player, question=selectDialogQuestion)
                        found = True
                    elif self.screen.matches (r'In what direction.*\?.*'):
                        matched = DirectionInteraction (player, self.screen.lastMatch())
                        found = True
                    elif self.screen.cursorY == 0:
                        # This can't be waiting for the player to move, we guess it's a free entry question
                        matched = FreeEntryInteraction (player, self.screen.getRow(0).strip())
                        found = True
                    #elif... select position with cursor interaction
                    #  Finally, assume the next turn is ready, and hand over control
                    else:
                        msg = self.screen.getRow(0).strip()
                        if len(msg) > 0:
                            info += [msg]
                        found = True
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

    def getArea (self, x=0, y=0, w=WIDTH, h=HEIGHT):
        """ Retrieve a rectangular area of the screen """
        return self.screen.getArea(x, y, w, h)

    def getRow (self, row, start=0, finish=WIDTH):
        """ Retrieve a row off the screen, or a substring of a row """
        return self.screen.getRow(row, start, finish)

    def cursorX (self):
        """ Retrieves the current X position of the cursor """
        return self.screen.cursorX

    def cursorY (self):
        """ Retrieves the current Y position of the cursor """
        return self.screen.cursorY

    def cellAt (self, x, y):
        """ Returns the current contents of the Cell at position (x, y) """
        return self.screen.screen[y][x]
        
    def interact(self):
        self.child.send (chr(18)) # CTRL+R to redraw screen
        self.child.interact (escape_character=chr(1)) # CTRL+A leaves interactive mode
        print "\n"*25
        self.child.send (chr(18))

class LocalNetHackConnection(NetHackConnection):
    def __init__(self, username=None):
        super (LocalNetHackConnection, self).__init__()
        self.username = username
        userstr = (not username is None) and ('-u ' + username) or ''
        self.child = pexpect.spawn ("nethack %s" % userstr)

    def __setstate__(self, state):
        """ FIXME: __setstate__ duplicates constructor functionallity """
        self.__dict__ = state
        userstr = (not self.username is None) and ('-u ' + self.username) or ''
        self.child = pexpect.spawn ("nethack %s" % userstr)
        self.patchEnvironment()

class RemoteNetHackConnection(NetHackConnection):
    def __init__(self, user=None, passwd=None, host=None):
        super (RemoteNetHackConnection, self).__init__()
        self.user = user
        self.passwd = passwd
        self.host = host
        self.child = pexpect.spawn ("telnet %s" % host)
        self.login()

    def __setstate__(self, state):
        """ FIXME: __setstate__ duplicates constructor functionallity """
        self.__dict__ = state
        self.child = pexpect.spawn ("telnet %s" % self.host)
        self.patchEnvironment()

    def parseOptions (self, sep, x, y, w, h):
        """ Parse an area of the screen as a list of options. Used for parsing
            DGameLaunch menus only for now """
        lines = self.screen.getArea (x, y, w, h)
        splits = [line.split(sep) for line in lines]
        strips = [(opt[1].strip().lower(), opt[0].strip())
                     for opt in splits if len(opt) == 2]
        return dict(strips)

    def login(self):
        """ Enter user/password credentials. """
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


