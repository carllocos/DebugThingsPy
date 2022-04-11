import sys
import logging
import inspect


logging.basicConfig(level=logging.DEBUG)

DEBUG = False

def dbgprint(s):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    cn =str(calframe[1][3])
    if DEBUG:
        _prefix = (cn + ':').upper()
        logging.debug(f'{_prefix} {s}')


def infoprint(s):
    print(f'[INFO] {s}')

def errprint(s):
    print(s)
    sys.exit()
