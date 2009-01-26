import re

WIDTH=80
HEIGHT=24

class Cell(object):
    def __init__(self, char=' '):
        self.char = char
        self.bold = False
        self.inverse = False
        self.foreground = 9
    def __str__ (self):
        result = ''
        someEscape = False
        if self.bold:
            result += '\x1b[1m'
            someEscape = True
        if self.inverse:
            result += '\x1b[7m'
            someEscape = True
        if self.foreground < 9:
            result += '\x1b[3%dm' % self.foreground
            someEscape = True
        result += self.char
        if someEscape:
            result += '\x1b[m'
        return result
    def set(self, char, bold, inverse, foreground):
        self.char = char
        self.bold = bold
        self.inverse = inverse
        self.foreground = foreground

class Screen(object):
    """ A Screen holds a bi-dimensional array of Cell that represents the state
        of each character on a 80x24 terminal.
        
        New output should be added via the printstr() method, passing in any
        output that has occurred, straight from the terminal.
        
        The state of the screen can be queried with the getArea(), getRow() and
        matches() methods"""
    def __init__(self):
        self.screen = [[Cell() for cell in range(WIDTH)] for x in range(HEIGHT + 1)]
        self.cursorX = 0
        self.cursorY = 0
        self.savedCursorX = 0
        self.savedCursorY = 0
        self.charSet = "default"
        self.G0 = "default"
        self.G1 = "default"
        self.charAttBold = False
        self.charAttInverse = False
        self.charAttForeground = 9
        self.escape_sequences = self.escapeSequenceDict()

    def __getstate__(self):
        state = dict(self.__dict__)
        del state['escape_sequences']
        return state

    def __setstate__(self, state):
        self.__dict__ = state
        self.escape_sequences = self.escapeSequenceDict()

    def escapeSequenceDict(self):
        """ Generate XTerm's escape secuences.
            This dictionary can be safely cached.
        """
        return {r'(\()(.)': self.setCharset, # Set G0 character set
                r'(\))(.)': self.setCharset, # Set G1 character set
                r'\[(\d+)d':self.gotoY, # Line position absolute
                r'\[(\d+);(\d+)H': self.gotoXY, # Goto position
                r"\[1;24r": self.ignore, # Set scrolling size of Window (1, 24)
                r"\[m": self.ignore, # Turn off character attributes
                r"\[\d+l": self.ignore, # Reset mode
                r"\[\?\d+h": self.ignore, # Set DEC private mode
                r"\[\?\d+l": self.ignore, # Reset DEC private mode
                r"=": self.ignore, # Set Application Keypad
                r">": self.ignore, # Set Normal Keypad
                r"\[H": self.gotoHome, # Move cursor to upper left corner
                r"\[2J": self.clearScreen, # Clear entire screen
                r"\[K": self.eraseToEndOfLine,
                r"\[A": self.cursorUp,
                r"\[C": self.cursorRight,
                r"\[(\d+)m": self.setCharacterAtts,
                r"\[m": self.resetCharAtts,
                r"7": self.saveCursor, # Save cursor position and attributes
                r"8": self.restoreCursor # Restore cursor position and attributes
               }

    def dump(self):
        """ Debugging method.
            Prints the whole screen (with formatting attributes and all).
        """
        for row in self.screen:
            print ''.join([str(cell) for cell in row])

    def printstr (self, cmd):
        """ Updates the state of the screen with a new chunk of output. """
        index = 0
        while index < len(cmd):
            if cmd[index] == '\x1b':
                index += 1
                found = False
                for seq in self.escape_sequences.keys():
                    match = re.match(seq, cmd[index:])
                    if not match is None:
                        self.escape_sequences[seq](match)
                        index += len(match.group(0))
                        found = True
                        break
                if not found:
                    print
                    print "Unhandled escape sequence."
                    raise ValueError, list(cmd[index-1:index+30])
            else:
                #print [cmd[index]], "=> printch",
                try:
                    self.printch(cmd[index])
                except IndexError:
                    print 'Attempted to print outside the screen!'
                    print 'Cursor X:', self.cursorX
                    print 'Cursor Y:', self.cursorY
                    print 'Current screen:'
                    for row in self.getArea():
                        print row
                    print 'Input string:'
                    print [cmd]
                    print 'Context:'
                    print [cmd[index-10:index]], "We're here!", [cmd[index:index+10]]
                    import pdb; pdb.set_trace()
                    raise
                index += 1

    def printch (self, ch):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        if self.cursorX >= WIDTH or self.cursorX < 0 or self.cursorY >= HEIGHT or self.cursorY < 0:
            raise IndexError
        if ch == '\r':
            self.cursorX = 0
        elif ch == '\n':
            self.cursorY += 1
        elif ch == '\x08': # Backspace
            self.cursorX -= 1
        elif ch == '\x0f': # Shift in - Invoke G0 charset
            self.charSet = self.G0
        elif ch >= ' ' and ch <= '~':
            self.screen[self.cursorY][self.cursorX].set(ch,
                                                        self.charAttBold,
                                                        self.charAttInverse,
                                                        self.charAttForeground)
            self.cursorX += 1
            if self.cursorX >= 80:
                if self.cursorY < HEIGHT - 1:
                    self.cursorY += 1
                self.cursorX = 0
        else:
            print 'not printable character', [ch]
        self.cursorY = min (self.cursorY, HEIGHT - 1)

    def gotoHome (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        self.cursorX = 0
        self.cursorY = 0

    def clearScreen (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        ## Shouldn't this send the cursor to (0,0) also??
        self.screen = [[Cell() for cell in range(WIDTH)] for x in range(HEIGHT + 1)]

    def leftN (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this.
            FIXME: This escape handler isn't bound to any escape sequence.
        """
        val = self.parseInt (cmd, 1)
        #print "Left", val
        self.cursorX -= val

    def gotoY (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        #print "gotoY", val
        self.cursorY = int(cmd.group(1)) - 1

    def gotoXY (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        self.cursorY = int(cmd.group(1)) - 1
        self.cursorX = int(cmd.group(2)) - 1

    def setCharset (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        charset = "default"
        if cmd.group(2) == '0':
            charset = "dec"
        elif cmd.group(2) == 'B':
            charset = "usascii"
        else:
            raise ValueError, "Unknown charset " + cmd
        if cmd.group(1) == '(':
            self.G0 = charset
        elif cmd.group(1) == ')':
            self.G1 = charset
        else:
            raise ValueError, "Unknown charset " + cmd

    def saveCursor (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        self.savedCursorX = self.cursorX
        self.savedCursorY = self.cursorY

    def restoreCursor (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        self.cursorX = self.savedCursorX
        self.cursorY = self.savedCursorY

    def cursorRight (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        self.cursorX += 1

    def cursorUp (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        self.cursorY -= 1

    def eraseToEndOfLine (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        for i in range(self.cursorX, WIDTH):
            self.screen[self.cursorY][i] = Cell()

    def insertLines (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this
            FIXME: This escape handler isn't bound to any escape sequence.
        """
        val = self.parseInt (cmd, 1)
        print "InsertLines", val
        self.screen = self.screen[:self.cursorY] + [[Cell() for cell in range(WIDTH)] for x in range(val)] + self.screen [self.cursorY:HEIGHT-val]

    def setCharacterAtts (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        val = int(cmd.group(1))
        if val == 0:
            self.resetCharAtts (cmd)
        elif val == 1:
            self.charAttBold = True
        elif val == 7:
            self.charAttInverse = True
        elif val >= 30 and val < 40:
            self.charAttForeground = val - 30
        else:
            print "In setCharacterAtts: Unrecognised attribute:", val


    def resetCharAtts (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        self.charAttBold = False
        self.charAttInverse = False
        self.charAttForeground = 9

    def ignore (self, cmd):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        pass

    def getArea (self, x=0, y=0, w=WIDTH, h=HEIGHT):
        """ Retrieve a rectangular area of the screen """
        return [''.join ([cell.char for cell in row[x:x+w]]) for row in self.screen[y:y+h]]

    def getRow (self, row, start=0, finish=WIDTH):
        """ Retrieve a row off the screen, or a substring of a row """
        result = ''.join ([cell.char for cell in self.screen[row][start:finish]])
        return result

    def getCharAtRelativePos (self, offsetX=0, offsetY=0):
        """ Internal auxiliary method.  You shouldn't need to invoke this """
        posX = self.cursorX + offsetX
        posY = self.cursorY + offsetY
        if posX < 0 or posX >= WIDTH or posY < 0 or posY >= HEIGHT:
            return None
        return self.screen[posY][posX].char

    def matches (self, pattern):
        """ Returns True if the string appearing right before the cursor matches
            'pattern'.
            Pattern can be any Python regular expression.
        """
        self._last_match = None
        toMatch = self.getRow (self.cursorY, finish=self.cursorX)
        if not pattern.endswith('$'):
            pattern = pattern + '$'
        match = re.search (pattern, toMatch)
        if not match is None:
            self._last_match = match
        return not self._last_match is None

    def lastMatch (self):
        """ Returns last match found by 'matches'.  Returns the exact string
            that matched, not the pattern """
        return getattr(self, '_last_match', None)

    def multiMatch (self, patterns):
        """ Returns the string that appears before the cursor that matches some
            pattern in 'patterns', or None if none match.
        """
        for pattern in patterns:
            if self.matches (pattern):
                return self._last_match
        return None

