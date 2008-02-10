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
        self.player.send ('\x0b')
        return self.player.watch()

class Information (object):
    """ I describe a bit of information the game reports.
        Unlike an interaction, I don't require an answer and can be discarded imediately"""
    def __init__ (self, player, message):
        checkPendingInteraction (player)
        self.message = message

class DirectionInteraction (Interaction):
    """ The player should choose a direction here """
    def answer (self, ans):
        super (DirectionInteraction, self).answer (keys.dirs[ans])
    def options (self):
        return keys.dirs.keys()

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
            self.answerDefault()
        else:
            super(YesNoInteraction, self).answer(ans)
    def options (self):
        """ Life is simple """
        return ["y", "n"]

class YesNoQuitInteraction (Interaction):
    """ I describe a yes/no/quit question.  These questions only arise once the game is over. """
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
            self.answerDefault()
        else:
            super(YesNoQuitInteraction, self).answer(ans)
    def options (self):
        """ Life is simple """
        return ["y", "n", "q"]

class SelectInteraction (Interaction):
    """ I describe a question where the user should select an item, usually from the inventory """
    def __init__ (self, player, question):
        super (SelectInteraction, self).__init__ (player, question)
        match = re.match (r'(?P<question>.*) \[(?P<opts>.*) or \?\*\] ', question)
        if not match is None:
            self.question = match.group ('question')
            self.opts = match.group ('opts')
    def options (self):
        return self.opts[:]

class MultipleSelectInteraction (Interaction):
    """ I describe a list of options from which you can select many alternatives """
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
        while more_pages:
            for line in lines:
                if line.find(' - ') == -1:
                    category = line.strip()
                else:
                    key, item = line.split(' - ', 1)
                    it = Item(key.strip(), description=item.strip(), category=category)
                    opts.append(it)
            if matched == '(1 of 2)':
                self.player.send ('>')
                matched = self.watch(['\(end\) ', '\(\d of \d\) '])
            else:
                more_pages = False
        self.opts = opts

    def options (self):
        return self.opts

    def answer (self, items):
        checkPendingInteraction (self.player, self)
        self.player.pendingInteraction = None
        for i in items:
            self.player.send (i['key'])
        self.player.send (' ')
        return self.player.watch()
