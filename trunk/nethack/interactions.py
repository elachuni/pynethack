import nethackkeys as keys
from items import Item, Spell
import re

class PendingInteraction (Exception):
    def __init__(self, interaction):
        self.interaction = interaction
    def __str__(self):
        return repr(self.interaction.question)

class InteractionNotPending (Exception):
    def __init__(self, interaction):
        self.interaction = interaction
    def __str__(self):
        return repr(self.interaction.question)

def checkPendingInteraction (server, interaction=None):
    """ Check that a NetHackConnection's pending interaction is what is should be.
        Raises an exception otherwise. """
    if interaction is None and not server.pendingInteraction is None:
        raise PendingInteraction (server.pendingInteraction)
    elif server.pendingInteraction != interaction:
        raise InteractionNotPending (interaction)

class Interaction (object):
    """ I describe an interactive question or dialog in the game.
        NetHackPlayer's methods return an Interaction when they need further input from the player
        to complete. """
    defaultAnswer = None
    def __init__ (self, server, question):
        checkPendingInteraction (server)
        self.server = server
        self.question = question
        server.pendingInteraction = self
    def answer (self, ans):
        checkPendingInteraction (self.server, self)
        self.server.pendingInteraction = None
        self.server.send (ans)
        return self.server.watch()
    def answerDefault (self):
        checkPendingInteraction (self.server, self)
        self.server.pendingInteraction = None
        self.server.send ('\x1b')
        return self.server.watch()
    def __str__ (self):
        return '<%s %s>' % (self.__class__.__name__, self.question)

class Information (object):
    """ I describe a bit of information the game reports.
        Unlike an interaction, I don't require an answer and can be discarded imediately"""
    def __init__ (self, server, message):
        #checkPendingInteraction (server)
        self.message = message
    def __str__ (self):
        return '\n'.join(self.message)

class DirectionInteraction (Interaction):
    """ The server should choose a direction here """
    def __init__ (self, server, question):
        super (DirectionInteraction, self).__init__ (server, question)
        match = re.match (r'(?P<question>.*) \[(?P<opts>.*)\] ', question)
        if match is None:
            self.options = keys.dirs.keys()
        else:
            self.question = match.group ('question')
            self.options = [opt[0] for opt in keys.dirs.items() if opt[1] in match.group ('opts')]

    def answer (self, ans):
        return super (DirectionInteraction, self).answer (keys.dirs[ans])

class YesNoInteraction (Interaction):
    """ I describe a yes/no question """
    __opts = {'yes': 'y', 'y': 'y', 'no': 'n', 'n': 'n'}
    def __init__ (self, server, question):
        super (YesNoInteraction, self).__init__(server, question)
        # Attempt to parse question in to question and default answer:
        match = re.match (r'(?P<question>.*) \[yn\]( \((?P<def>.)\))?', question)
        if not match is None:
            self.question = match.group ('question')
            self.defaultAnswer = match.group ('def')
    def answer (self, ans):
        ans = self.__opts.get(ans)
        if ans is None:
            match = self.answerDefault()
        else:
            match = super(YesNoInteraction, self).answer(ans)
        return match
    options = ["y", "n"]

class CursorPointInteraction (Interaction):
    """ I'm an interaction that requests the user to select a position in the maze using the cursor. """
    def answer (self, x, y):
        checkPendingInteraction (self.server, self)
        self.server.pendingInteraction = None
        currentX = self.server.x()
        currentY = self.server.y()
        while x > currentX:
            self.server.send ('l')
            currentX += 1
        while x < currentX:
            self.server.send ('h')
            currentX -= 1
        while y < currentY:
            self.server.send ('k')
            currentY -= 1
        while y > currentY:
            self.server.send ('j')
            currentY += 1
        self.server.send ('.')
        return self.server.watch()

class YesNoQuitInteraction (Interaction):
    """ I describe a yes/no/quit question. """
    __opts = {'yes': 'y', 'y': 'y', 'no': 'n', 'n': 'n', 'quit': 'q', 'q': 'q'}
    defaultAnswer = 'q'
    def __init__ (self, server, question):
        super (YesNoQuitInteraction, self).__init__(server, question)
        # Attempt to parse question in to question and default answer:
        match = re.match (r'(?P<question>.*) \[ynq\]( \((?P<def>.)\))?', question)
        if not match is None:
            self.question = match.group ('question')
            self.defaultAnswer = match.group ('def')
    def answer (self, ans):
        ans = self.__opts.get(ans.lower())
        if ans is None:
            match = self.answerDefault()
        else:
            match = super(YesNoQuitInteraction, self).answer(ans)
        return match
    options = ["y", "n", "q"]

class FreeEntryInteraction (Interaction):
    """ I describe a prompt to enter some free text. """
    def answer (self, ans):
        checkPendingInteraction (self.server, self)
        self.server.pendingInteraction = None
        self.server.sendline (ans)
        return self.server.watch()

class SelectInteraction (Interaction):
    """ I describe a question where the user should select an item, usually from the inventory """
    def __init__ (self, server, question):
        super (SelectInteraction, self).__init__ (server, question)
        match = re.match (r'(?P<question>.*) \[(?P<opts>.*) or \?\*\] ', question)
        if not match is None:
            self.question = match.group ('question')
            self.options = [Item(key) for key in match.group ('opts')] + [Item('*'), Item('?')]
        else:
            self.options = []
    def answer (self, item):
        checkPendingInteraction (self.server, self)
        self.server.pendingInteraction = None
        self.server.send (item.key)
        return self.server.watch(selectDialogQuestion=self.question)

class SelectDialogInteraction (Interaction):
    """ I describe a list of options from which you can select one or many alternatives.
        MultiSelect and SingleSelect dialogs aren't distinguishable at sight, so you need
        to tell me if I should treat this as a MultiSelect or a SingleSelect when you go to
        answer the question."""
    def __init__ (self, server, question=None):
        """ If question is None, I suppose it's on the first line of the screen. """
        Interaction.__init__(self, server, question)
        self.server = server
        if question is None:
            self.question = self.server.getRow(0).strip()
        matched = self.server.screen.multiMatch (['\(end\) ', '\(\d of \d\) '])
        if matched is None:
            raise ValueError, "No multiple selection dialog visible"
        lines = self.server.getArea (self.server.screen.cursorX - len(matched), 0, h=self.server.screen.cursorY)
        opts = []
        more_pages = True
        totalPages = 0
        spellList = False
        while more_pages:
            for line in lines:
                if line.find(' - ') == -1:
                    category = line.strip()
                    if min([x in category for x in ['Name', 'Level', 'Category', 'Fail']]):
                        # Oi, this isn't an item list, it's a spell list!
                        spellList = True
                else:
                    key, item = line.split(' - ', 1)
                    if spellList:
                        it = Spell(key.strip(), description=item.strip(), headings=category)
                    else:
                        it = Item(key.strip(), description=item.strip(), category=category)
                    opts.append(it)
            if matched != '(end) ':
                currentPage, totalPages = self.parseMOfN (matched)
                print "Page", currentPage, "of", totalPages
                if currentPage < totalPages:
                    self.server.send ('>')
                    matched = self.server.watch(['\(end\) ', '\(\d of \d\) '])
                    if matched is None:
                        raise ValueError, "No multiple selection dialog visible"
                    lines = self.screen.getArea (self.server.screen.cursorX - len(matched), 0, h=self.server.screen.cursorY)
                else:
                    more_pages = False
            else:
                more_pages = False
        # Return to the first page
        for i in range(totalPages - 1):
            self.send ('<')
            self.server.watch (['\(end\) ', '\(\d of \d\) '])
        self.options = opts

    def answer (self, items):
        """ 'items': can be a single Item, or a list of Items.
            if it's a single Item then the dialog is treated as a SingleSelect dialog.
            if you pass in a list of items, I treat the list as a MultiSelect dialog."""
        checkPendingInteraction (self.server, self)
        self.server.pendingInteraction = None
        if isinstance (items, list):
            match = self.server.screen.multiMatch (['\(end\) ', '\(\d of \d\) '])
            if match == '(end) ':
                totalPages = 1
            else:
                currentPage, totalPages = self.parseMOfN(match)
                if currentPage != 1:
                    raise ValueError, "I shouldn't be asked to answer an interaction when not on the first page of a dialog."
            for page in range(totalPages):
                for i in items:
                    self.server.send (i.key)
                self.server.send (' ')
        else:
            self.server.send (items.key)
        return self.server.watch()
