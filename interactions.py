import nethackkeys as keys
from items import Item
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

def checkPendingInteraction (player, interaction=None):
    """ Check that a NetHackPlayer's pending interaction is what is should be.
        Raises an exception otherwise. """
    if interaction is None and not player.pendingInteraction is None:
        raise PendingInteraction (player.pendingInteraction)
    elif player.pendingInteraction != interaction:
        raise InteractionNotPending (interaction)

class Interaction (object):
    """ I describe an interactive question or dialog in the game.
        NetHackPlayer's methods return an Interaction when they need further input from the player
        to complete. """
    defaultAnswer = None
    def __init__ (self, player, question):
        checkPendingInteraction (player)
        self.player = player
        self.question = question
        player.pendingInteraction = self
    def answer (self, ans):
        checkPendingInteraction (self.player, self)
        self.player.pendingInteraction = None
        self.player.send (ans)
        return self.player.watch()
    def answerDefault (self):
        checkPendingInteraction (self.player, self)
        self.player.pendingInteraction = None
        self.player.send ('\x1b')
        return self.player.watch()

class Information (object):
    """ I describe a bit of information the game reports.
        Unlike an interaction, I don't require an answer and can be discarded imediately"""
    def __init__ (self, player, message):
        #checkPendingInteraction (player)
        self.message = message

class DirectionInteraction (Interaction):
    """ The player should choose a direction here """
    def __init__ (self, player, question):
        super (DirectionInteraction, self).__init__ (player, question)
        match = re.match (r'(?P<question>.*) \[(?P<opts>.*)\] ', question)
        if match is None:
            self.__opts = keys.dirs.keys()
        else:
            self.question = match.group ('question')
            self.__opts = [opt[0] for opt in keys.dirs.items() if opt[1] in match.group ('opts')]

    def answer (self, ans):
        return super (DirectionInteraction, self).answer (keys.dirs[ans])
    def options (self):
        return self.__opts[:]

class YesNoInteraction (Interaction):
    """ I describe a yes/no question """
    __opts = {'yes': 'y', 'y': 'y', 'no': 'n', 'n': 'n'}
    def __init__ (self, player, question):
        super (YesNoInteraction, self).__init__(player, question)
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
    def options (self):
        """ Life is simple """
        return ["y", "n"]

class CursorPointInteraction (Interaction):
    """ I'm an interaction that requests the user to select a position in the maze using the cursor. """
    def answer (self, x, y):
        checkPendingInteraction (self.player, self)
        self.player.pendingInteraction = None
        currentX = self.player.x()
        currentY = self.player.y()
        while x > currentX:
            self.player.send ('l')
            currentX += 1
        while x < currentX:
            self.player.send ('h')
            currentX -= 1
        while y < currentY:
            self.player.send ('k')
            currentY -= 1
        while y > currentY:
            self.player.send ('j')
            currentY += 1
        self.player.send ('.')
        return self.player.watch()

class YesNoQuitInteraction (Interaction):
    """ I describe a yes/no/quit question. """
    __opts = {'yes': 'y', 'y': 'y', 'no': 'n', 'n': 'n', 'quit': 'q', 'q': 'q'}
    defaultAnswer = 'q'
    def __init__ (self, player, question):
        super (YesNoQuitInteraction, self).__init__(player, question)
        # Attempt to parse question in to question and default answer:
        match = re.match (r'(?P<question>.*) \[ynq\]( \((?P<def>.)\))?', question)
        if not match is None:
            self.question = match.group ('question')
            self.defaultAnswer = match.group ('def')
    def answer (self, ans):
        ans = self.__opts.get(ans)
        if ans is None:
            match = self.answerDefault()
        else:
            match = super(YesNoQuitInteraction, self).answer(ans)
        return match
    def options (self):
        """ Life is simple """
        return ["y", "n", "q"]

class FreeEntryInteraction (Interaction):
    """ I describe a prompt to enter some free text. """
    def answer (self, ans):
        checkPendingInteraction (self.player, self)
        self.player.pendingInteraction = None
        self.player.sendline (ans)
        return self.player.watch()

class SelectInteraction (Interaction):
    """ I describe a question where the user should select an item, usually from the inventory """
    def __init__ (self, player, question):
        super (SelectInteraction, self).__init__ (player, question)
        match = re.match (r'(?P<question>.*) \[(?P<opts>.*) or \?\*\] ', question)
        if not match is None:
            self.question = match.group ('question')
            self.__opts = match.group ('opts')
    def options (self):
        return self.__opts[:]

class SelectDialogInteraction (Interaction):
    """ I describe a list of options from which you can select one or many alternatives.
        MultiSelect and SingleSelect dialogs aren't distinguishable at sight, so you need
        to tell me if I should treat this as a MultiSelect or a SingleSelect when you go to
        answer the question."""
    def __init__ (self, player, question=None):
        """ If question is None, I suppose it's on the first line of the screen. """
        Interaction.__init__(self, player, question)
        if question is None:
            self.question = self.player.screen.getRow(0).strip()
        matched = self.player.screen.multiMatch (['\(end\) ', '\(\d of \d\) '])
        if matched is None:
            raise ValueError, "No multiple selection dialog visible"
        lines = self.player.screen.getArea (self.player.screen.cursorX - len(matched), 0, h=self.player.screen.cursorY)
        opts = []
        more_pages = True
        totalPages = 0
        while more_pages:
            for line in lines:
                if line.find(' - ') == -1:
                    category = line.strip()
                else:
                    key, item = line.split(' - ', 1)
                    it = Item(key.strip(), description=item.strip(), category=category)
                    opts.append(it)
            if matched != '(end) ':
                currentPage, totalPages = self.parseMOfN (matched)
                print "Page", currentPage, "of", totalPages
                if currentPage < totalPages:
                    self.player.send ('>')
                    matched = self.player.watch(['\(end\) ', '\(\d of \d\) '])
                    if matched is None:
                        raise ValueError, "No multiple selection dialog visible"
                    lines = self.player.screen.getArea (self.player.screen.cursorX - len(matched), 0, h=self.player.screen.cursorY)
                else:
                    more_pages = False
            else:
                more_pages = False
        # Return to the first page
        for i in range(totalPages - 1):
            self.send ('<')
            self.player.watch (['\(end\) ', '\(\d of \d\) '])
        self.__opts = opts

    def options (self):
        return self.__opts[:]

    def answer (self, items):
        """ 'items': can be a single Item, or a list of Items.
            if it's a single Item then the dialog is treated as a SingleSelect dialog.
            if you pass in a list of items, I treat the list as a MultiSelect dialog."""
        checkPendingInteraction (self.player, self)
        self.player.pendingInteraction = None
        if isinstance (items, Item):
            self.player.send (items.key)
        else:
            match = self.player.screen.multiMatch (['\(end\) ', '\(\d of \d\) '])
            if match == '(end) ':
                totalPages = 1
            else:
                currentPage, totalPages = self.parseMOfN(match)
                if currentPage != 1:
                    raise ValueError, "I shouldn't be asked to answer an interaction when not on the first page of a dialog."
            for page in range(totalPages):
                for i in items:
                    self.player.send (i.key)
                self.player.send (' ')
        return self.player.watch()
