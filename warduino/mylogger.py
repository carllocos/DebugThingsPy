import sys
import inspect
import logging

DEBUG = False


def stderr_print(s):
    globals, DEBUG

    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    cn = str(calframe[1][3])
    if DEBUG:  # and cn in ONLY:
        print((cn + ":").upper(), s, file=sys.stderr)


def errprint(s):
    print(s)
    sys.exit()


def get_logger(name):
    logger = logging.getLogger(name)
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s - %(message)s"))
    logger.addHandler(c_handler)
    logger.propagate = False
    logger.setLevel(logging.INFO)
    return logger
