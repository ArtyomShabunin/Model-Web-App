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
    def __init__(self, queue: asyncio.Queue, loop: asyncio.BaseEventLoop, observer, paths: list,
                 *args, **kwargs):
        self._loop = loop
        self._queue = queue
        # self.counter = 0
        # self._paths = {k:False for k in paths}

        # self.observer = observer

        self.activ_paths = set()

        self.prev_time = time.time()

        super(*args, **kwargs)

    def on_created(self, event: FileSystemEvent) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

        self.activ_paths.add(os.path.dirname(event.src_path))
        self.prev_time = time.time()

        # self._paths[os.path.dirname(event.src_path)] = True
        # self._time = time.time()
        #
        # print("Список директорий")
        # for i in self._paths:
        #     print(f'{i}: {self._paths[i]}')

        # self._paths.pop(self._paths.index(os.path.dirname(event.src_path)))

        # if not paths:
        #     self._loop.call_soon_threadsafe(self._queue.put_nowait, 'Stop Observer')
        #     print('Stop Observer')
        #     self.observer.stop()


    def on_modified(self, event: FileSystemEvent) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

        self.activ_paths.add(os.path.dirname(event.src_path))
        self.prev_time = time.time()

        # self._paths.pop(self._paths.index(os.path.dirname(event.src_path)))
        #
        # if not self._paths:
        #     self._loop.call_soon_threadsafe(self._queue.put_nowait, 'Stop Observer')
        #     print('Stop Observer')
        #     self.observer.stop()


class EventIterator(object):

    def __init__(self, queue: asyncio.Queue,
                 loop: Optional[asyncio.BaseEventLoop] = None):
        self.queue = queue

    def __aiter__(self):
        self._time = time.time()
        return self

    async def __anext__(self):
        item = await self.queue.get()

        if str(item) == 'Stop Observer':
            print('StopAsyncIteration')
            raise StopAsyncIteration

        return item

class RestartsWatcher():
    def __init__(self):
        pass

    def watch(self, paths: list, queue: asyncio.Queue, loop: asyncio.BaseEventLoop,
              recursive: bool = False) -> None:
        """Watch a directory for changes."""

        self.observer = Observer()
        self.handler = _EventHandler(queue, loop, self.observer, paths)

        self.observers = []

        for path in paths:
            print(f'Путь: {path}')
            self.observer.schedule(self.handler, path, recursive=recursive)
            self.observers.append(self.observer)

            # handler.counter = handler.counter + 1


        self.observer.start()
        print("Observer started")
        # print(queue)
        # print(dir(queue))
        # observer.join(10)
        # loop.call_soon_threadsafe(queue.put_nowait, None)

async def make_restart_copy(model_name, location):
    file_time = time.localtime(time.time())
    file_name = rf'{model_name}_{file_time.tm_year}_{file_time.tm_mon}_{file_time.tm_mday}_{file_time.tm_hour}_{file_time.tm_min}_{file_time.tm_sec}.rst'
    new_file_dir = r'\\'.join(location.split('\\')[0:-1]+['temp_restarts', file_name])

    os.makedirs(os.path.dirname(new_file_dir), exist_ok=True)
    print(f'Должна была появиться директория {os.path.dirname(new_file_dir)}')
    shutil.copy(os.path.abspath(location), os.path.abspath(new_file_dir))

    print(f'File copy made - "{new_file_dir}"')
    pass

async def consume(queue: asyncio.Queue, model_name) -> None:
    async for event in EventIterator(queue):
        if event is not None:
            print(f'Got an event!\nevent type: {event.event_type}  path : {event.src_path}')
            # await make_restart_copy(model_name, event.src_path)
        else:
            print(event)
