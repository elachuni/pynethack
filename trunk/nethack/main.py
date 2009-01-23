#
# PyNethack is not a program.  This is just a sample of how to use it.
# You should define your own nethack player (see examples.py on how to do that)
#

from examples import Explorer
from connection import LocalNetHackConnection

if __name__ == '__main__':
    conn = LocalNetHackConnection()
    conn.echo = True
    a = Explorer(conn)
    a.play()
    a.run()
