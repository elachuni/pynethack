BOLD = 1

FGBLACK = 0 << 5
FGRED = 1 << 5
FGGREEN = 2 << 5
FGYELLOW = 3 << 5
FGBLUE = 4 << 5
FGMAGENTA = 5 << 5
FGCYAN = 6 << 5
FGWHITE = 7 << 5

WIDTH=80
HEIGHT=24

class Screen(object):
    def __init__(self):
        self.screen = [[' '] * WIDTH for x in range(HEIGHT)]
        self.attrs = [[0] * WIDTH for x in range(HEIGHT)]
        self.cursorX = 0
        self.cursorY = 0
        self.charSet = "default"
        self.G0 = "default"
        self.G1 = "default"
        self.charAtts = 0
        self.escape_sequences = {"( ": self.setCharset, # Set G0 character set
                                 ") ": self.setCharset, # Set G1 character set
                                 "[$d":self.gotoY, # Line position absolute
                                 "[$;$H": self.gotoXY, # Goto position
                                 "[1;24r": self.ignore, # Set scrolling size of Window (1, 24)
                                 "[m": self.ignore, # Turn off character attributes
                                 "[$l": self.ignore, # Reset mode
                                 "[?$h": self.ignore, # Set DEC private mode
                                 "[?$l": self.ignore, # Reset DEC private mode
                                 "=": self.ignore, # Set Application Keypad
                                 ">": self.ignore, # Set Normal Keypad
                                 "[H": self.gotoHome, # Move cursor to upper left corner
                                 "[2J": self.clearScreen, # Clear entire screen
                                 "[K": self.eraseToEndOfLine,
                                 "[A": self.cursorUp,
                                 "[C": self.cursorRight,
                                 "[$m": self.setCharacterAtts,
                                 "[m": self.resetCharAtts,
                                }

    def dump(self):
        for row in self.screen:
            print ''.join(row)

    def printstr (self, cmd):
        index = 0
        while index < len(cmd):
            if cmd[index] == '\x1b':
                index += 1
                found = False
                for seq in self.escape_sequences.keys():
                    subidx = index
                    seqidx = 0
                    while seqidx < len(seq):
                        if seq[seqidx] == '$' and cmd[subidx].isdigit():
                            while cmd[subidx].isdigit():
                                subidx += 1
                            seqidx += 1
                        elif seq[seqidx] == ' ' or seq[seqidx] == cmd[subidx]:
                            seqidx += 1
                            subidx += 1
                        else:
                            break
                    if seqidx == len(seq):
                        #print [cmd[index:subidx]], "=>", self.escape_sequences[seq].__name__
                        self.escape_sequences[seq](cmd[index:subidx])
                        index = subidx
                        found = True
                        break
                if not found:
                    print
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
                    raise
                index += 1

    def printch (self, ch):
        if self.cursorX >= WIDTH or self.cursorX < 0 or self.cursorY >= HEIGHT or self.cursorY < 0:
            raise IndexError
        if ch == '\r':
            self.cursorX = 0
            self.cursorY += 1
        elif ch == '\n':
            pass # Use '\r' for newlines
        elif ch == '\x08': # Backspace
            self.cursorX -= 1
        elif ch == '\x0f': # Shift in - Invoke G0 charset
            self.charSet = self.G0
        elif ch >= ' ' and ch <= '~':
            self.screen[self.cursorY][self.cursorX] = ch
            self.attrs[self.cursorY][self.cursorX] = self.charAtts
            self.cursorX += 1
            if self.cursorX >= 80:
                self.cursorY += 1
                self.cursorX = 0
        else:
            print 'not printable character', [ch]
        self.cursorY = min (self.cursorY, HEIGHT - 1)

    def gotoHome (self, cmd):
        self.cursorX = 0
        self.cursorY = 0

    def clearScreen (self, cmd):
        self.screen = [[' '] * WIDTH for x in range(HEIGHT)]
        self.attrs = [[0] * WIDTH for x in range(HEIGHT)]

    def leftN (self, cmd):
        val = self.parseInt (cmd, 1)
        #print "Left", val
        self.cursorX -= val

    def gotoY (self, cmd):
        val = self.parseInt (cmd, 1)
        #print "gotoY", val
        self.cursorY = val - 1

    def gotoXY (self, cmd):
        row = self.parseInt (cmd, 1)
        col = self.parseInt (cmd, cmd.index(';') + 1)
        #print "gotoXY", row, col
        self.cursorY = row - 1
        self.cursorX = col - 1

    def setCharset (self, cmd):
        charset = "default"
        if cmd[1] == '0':
            charset = "dec"
        elif cmd[1] == 'B':
            charset = "usascii"
        else:
            raise ValueError, "Unknown charset " + cmd
        if cmd[0] == '(':
            self.G0 = charset
        elif cmd[0] == ')':
            self.G1 = charset
        else:
            raise ValueError, "Unknown charset " + cmd

    def cursorRight (self, cmd):
        self.cursorX += 1

    def cursorUp (self, cmd):
        self.cursorY -= 1

    def eraseToEndOfLine (self, cmd):
        for i in range(self.cursorX, WIDTH):
            self.screen[self.cursorY][i] = ' '
            self.attrs[self.cursorY][i] = 0

    def insertLines (self, cmd):
        val = self.parseInt (cmd, 1)
        print "InsertLines", val
        self.screen = self.screen[:self.cursorY] + [[' '] * WIDTH for x in range(val)] + self.screen [self.cursorY:HEIGHT-val]

    def setCharacterAtts (self, cmd):
        val = self.parseInt (cmd, 1)
        if val == 1:
            self.charAtts |= BOLD
        elif val >= 30 and val <= 37:
            self.charAtts &= ~(7<<5)
            self.charAtts |= (val - 30) << 5

    def resetCharAtts (self, cmd):
        self.charAtts = 0

    def ignore (self, cmd):
        pass

    def parseInt (self, cmd, startAt=0):
        idx = startAt + 1
        val = int(cmd[startAt])
        while cmd[idx].isdigit():
            val = val * 10 + int(cmd[idx])
            idx += 1
        return val

    def getArea (self, x=1, y=1, w=WIDTH, h=HEIGHT):
        return [''.join (row[x:x+w]) for row in self.screen[y:y+h]]

    def getRow (self, row, start=0, finish=WIDTH):
        result = ''.join (self.screen[row][start:finish])
        return result

    def getCharAtRelativePos (self, offsetX=0, offsetY=0):
        posX = self.cursorX + offsetX
        posY = self.cursorY + offsetY
        if posX < 0 or posX >= WIDTH or posY < 0 or posY >= HEIGHT:
            return None
        return self.screen[posY][posX]