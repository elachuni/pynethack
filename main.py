#
# PyNethack is not a program.  This is just a sample of how to use it.
# You should define your own nethack player (see examples.py on how to do that)
#

from examples import Introspective

if __name__ == '__main__':
    a = Introspective()
    a.login()
    a.new_game()
    a.run()
