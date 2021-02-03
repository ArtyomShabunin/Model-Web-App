import asyncio
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

import os
import time
import shutil
import glob
import copy


class _EventHandler(FileSystemEventHandler):
    def __init__(self, queue: asyncio.Queue, loop: asyncio.BaseEventLoop, observer,
                 *args, **kwargs):
        self._loop = loop
        self._queue = queue
        super(*args, **kwargs)

    def on_created(self, event: FileSystemEvent) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

class EventIterator(object):

    def __init__(self, queue: asyncio.Queue,
                 loop: Optional[asyncio.BaseEventLoop] = None):
        self.queue = queue

    def __aiter__(self):
        self._time = time.time()
        return self

    async def __anext__(self):
        item = await self.queue.get()
        #
        # if str(item) == 'Stop Observer':
        #     print('StopAsyncIteration')
        #     raise StopAsyncIteration

        return item

class RestartsWatcher():
    def __init__(self):
        pass

    def watch(self, paths: list, queue: asyncio.Queue, loop: asyncio.BaseEventLoop,
              recursive: bool = False) -> None:
        """Watch a directory for changes."""

        self.observer = Observer()
        handler = _EventHandler(queue, loop, self.observer)
        self.observers = []

        for path in paths:
            print(f'Путь: {path}')
            self.observer.schedule(handler, path, recursive=recursive)
            self.observers.append(self.observer)

        self.observer.start()
        print("Observer started")
        # print(queue)
        # print(dir(queue))
        # observer.join(10)
        # loop.call_soon_threadsafe(queue.put_nowait, None)


async def make_restart_copy(model_name, location):
    file_time = time.localtime(time.time())
    file_name = rf'{model_name}_{file_time.tm_year}_{str(file_time.tm_mon).zfill(2)}_{str(file_time.tm_mday).zfill(2)}_{str(file_time.tm_hour).zfill(2)}_{str(file_time.tm_min).zfill(2)}_{str(file_time.tm_sec).zfill(2)}'
    full_name = os.path.basename(location).replace('restart', file_name)

    new_file_dir = r'\\'.join(os.path.dirname(location).split('\\')[0:-1]+['temp_restarts', full_name])

    os.makedirs(os.path.dirname(new_file_dir), exist_ok=True)
    print(f'Должна была появиться директория {os.path.dirname(new_file_dir)}')
    shutil.copy(os.path.abspath(location), os.path.abspath(new_file_dir))

    print(f'File copy made - "{new_file_dir}"')
    pass

async def consume(queue: asyncio.Queue, prev_time, restarts_paths) -> None:
    async for event in EventIterator(queue):
        if event is not None:
            restarts_paths.add(event.src_path)
            prev_time = time.time()
        else:
            print(event)
