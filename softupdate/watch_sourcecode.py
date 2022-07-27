from __future__ import annotations
import os
from pathlib import PurePath
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils import get_logger
from web_assembly import WAModule
from utils import wat2wasm


class EventHandler(FileSystemEventHandler):
    Busy = False
    logger = None
    File = ""

    # def __init__(self, file, logger) -> None:
    #     super().__init__()
    #     self.__filepath = file
    #     self.__filename = os.path.basename(file)
    #     self.logger = logger

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        if event.event_type == "modified":
            src = os.path.basename(event.src_path)
            if src != EventHandler.File:
                return
            print("Change Detected on % s" % EventHandler.File)
            EventHandler.Busy = True
            mod = WAModule.from_file(event.src_path)
            mod.compile(cache=True)

            # Event is modified, you can process it now


class SourceWatcher:
    # Set the directory on watch
    logger = get_logger("SourceWatcher")

    def __init__(self, filepath):
        self.__filepath = filepath
        self.__filename = os.path.basename(filepath)
        self.__directory = os.path.dirname(self.__filepath)
        self.observer = Observer()

    def run(self):
        SourceWatcher.logger.info(f"Monitoring {self.__filepath}")
        EventHandler.File = self.__filename
        EventHandler.Logger = SourceWatcher.logger
        event_handler = EventHandler()
        self.observer.schedule(event_handler, self.__directory, recursive=True)
        self.observer.start()

    def stop(self):
        SourceWatcher.logger.info("Observer Stopped")
        self.observer.stop()
        self.observer.join()
