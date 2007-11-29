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
    def __init__ (self, player, question):
        checkPendingInteraction (player)
        self.player = player
        self.question = question
        player.pendingInteraction = self
    def answerDefault (self):
        checkPendingInteraction (self.player, self)
        self.player.pendingInteraction = None
        self.player.send ('\x0b')
        self.player.watch()

class YesNoInteraction (Interaction):
    """ I describe a yes/no question """
    def answer (self, ans):
        checkPendingInteraction (self.player, self)
        self.player.pendingInteraction = None
        if ans.lower() in ["yes", "y"]:
            self.player.send ('y')
        elif ans.lower in ["no", "n"]:
            self.player.send ('n')
        else:
            # Take default option
            self.player.sendline ('')
        self.player.watch()

    def answerDefault (self):
        checkPendingInteraction (self.player, self)
        self.player.pendingInteraction = None
        self.player.sendline ('')
        self.player.watch()

    def options (self):
        """ Life is simple """
        return ["Yes", "No"]

class MultipleSelectInteraction (Interaction):
    """ I describe a list of options from which you can select many alternatives """
    def __init__ (self, player, question=None):
        """ If question is None, I suppose it's on the first line of the screen. """
        Interaction.__init__(self, player, question)
        if question is None:
            self.question = self.player.screen.getRow(0).strip()
        matched = self.player.screen.multiMatch (['(end) ', '(# of #)'])
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
                    opts.append({'key': key.strip(), 'description':item.strip(), 'category': category})
            if matched == '(1 of 2)':
                self.player.send ('>')
                matched = self.watch(['(end) ', '(1 of 2)', '(2 of 2)'])
                    # We need a bit more power in our patterns here!
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
        self.player.watch()