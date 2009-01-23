# To use the functions in this file you'll need to make your savegame folder
# world-writeable, and set the SAVEGAME_DIR variable

SAVEGAME_DIR = '/var/games/nethack/save'

import pickle
from nethack import NetHackPlayer
import os

def serialize(player, filename):
    """ Serialize the NetHackPlayer in to a file, then save """
    f = open(filename, 'w')
    playerData = pickle.dumps(player)
    oldContents = os.listdir(SAVEGAME_DIR)
    player.save()
    for savegame in os.listdir(SAVEGAME_DIR):
        if not savegame in oldContents:
            saveGameData = open(SAVEGAME_DIR + '/' + savegame).read()
            break
    pickle.dump((playerData, saveGameData, savegame), f)

def unserialize(filename):
    """ Unserialize a NetHackPlayer from a file """
    f = open(filename)
    playerData, saveGameData, savegame = pickle.load(f)
    player = pickle.loads(playerData)
    g = open(SAVEGAME_DIR + '/' + savegame, 'w')
    g.write(saveGameData)
    g.close()
    player.play()
    return player

