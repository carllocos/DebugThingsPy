import sys
import inspect

DEBUG = False


def stderr_print(s):
    globals, DEBUG

    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    cn = str(calframe[1][3])
    if DEBUG:  # and cn in ONLY:
        print((cn + ':').upper(), s, file=sys.stderr)


def errprint(s):
    print(s)
    sys.exit()
