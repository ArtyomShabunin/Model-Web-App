import asyncio
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class _EventHandler(FileSystemEventHandler):
    def __init__(self, queue: asyncio.Queue, loop: asyncio.BaseEventLoop, observer,
                 *args, **kwargs):
        self._loop = loop
        self._queue = queue
        self.counter = 0

        self.observer = observer

        super(*args, **kwargs)

    def on_created(self, event: FileSystemEvent) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)
        print(f'event type: {event.event_type}  path : {event.src_path}')
        print(f'Очередь: {self._queue}')
        self.counter = self.counter - 1
        print(f'Счетчик = {self.counter}')


    def on_modified(self, event: FileSystemEvent) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)
        print(f'event type: {event.event_type}  path : {event.src_path}')
        self.counter = self.counter - 1
        print(f'Счетчик = {self.counter}')
        if self.counter < 1:
            print('Остановить Observer')
            self.observer.stop()



class EventIterator(object):

    def __init__(self, queue: asyncio.Queue,
                 loop: Optional[asyncio.BaseEventLoop] = None):
        self.queue = queue

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self.queue.get()

        if item is None:
            raise StopAsyncIteration

        return item


def watch(paths: list, queue: asyncio.Queue, loop: asyncio.BaseEventLoop,
          recursive: bool = False) -> None:
    """Watch a directory for changes."""

    observer = Observer()
    handler = _EventHandler(queue, loop, observer)

    observers = []

    for path in paths:
        print(f'Путь: {path}')
        observer.schedule(handler, path, recursive=recursive)
        observers.append(observer)

        handler.counter = handler.counter + 1


    observer.start()
    print("Observer started")
    print(queue)
    print(dir(queue))
    observer.join(10)
    loop.call_soon_threadsafe(queue.put_nowait, None)


async def consume(queue: asyncio.Queue) -> None:
    async for event in EventIterator(queue):
        print("Got an event!", event)
