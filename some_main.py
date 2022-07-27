import os
import time
from softupdate import SourceWatcher

if __name__ == "__main__":
    sw = SourceWatcher(os.getcwd() + "/test.wat")
    sw.run()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sw.stop()
