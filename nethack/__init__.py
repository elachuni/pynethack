from nethack import NetHackPlayer
from connection import LocalNetHackConnection, RemoteNetHackConnection

def connectLocal(player=None):
    
    if player is None:
        player = NetHack
