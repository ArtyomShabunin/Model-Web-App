import asyncio
from watchgod import awatch
import glob
import time
import shutil
import os
from functools import reduce
from collections import Counter

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

async def some_async_handler(event):
    print(f'event type: {event.event_type}  path : {event.src_path}')

class RestartsHandler(FileSystemEventHandler):
    def __init__(self, loop, *args, **kwargs):
        self._loop = loop
        super().__init__(*args, **kwargs)

    def on_modified(self, event):
        print(f'event type: {event.event_type}  path : {event.src_path}')

    def on_deleted(self, event):
        print(f'event type: {event.event_type}  path : {event.src_path}')




async def watch(model_name, dir):
   async for changes in awatch(dir):
       for status, location in changes:

           print(f'File "{location}" - {status.name}')

           if status.name == 'modified' or status.name == 'added':
               file_time = time.localtime(time.time())
               file_name = f'{model_name}_{file_time.tm_year}_{file_time.tm_mon}_{file_time.tm_mday}_{file_time.tm_hour}_{file_time.tm_min}_{file_time.tm_sec}.rst'
               new_file_dir = '\\'.join(location.split('\\')[0:-1]+['..', 'temp_restarts', file_name])

               os.makedirs(os.path.dirname(new_file_dir), exist_ok=True)
               shutil.copy(os.path.abspath(location), os.path.abspath(new_file_dir))

               print(f'File copy made - "{new_file_dir}"')

async def watch_restarts(model_name, dir_list):
    tasks = [asyncio.ensure_future(watch(model_name, i)) for i in dir_list]
    await asyncio.wait(tasks)

def clear_temp_restarts():
    dir_list = glob.glob('./**/temp_restarts', recursive=True)
    for folder in dir_list:
        shutil.rmtree(os.path.abspath(folder))

def show_restarts_list(dir_list):
    prj_count = len(dir_list)
    res_list = []
    for d in dir_list:
        res_list.append(glob.glob(os.path.join(d, '*.rst'), recursive=True))

    res_list = reduce(lambda x,y :x+y, res_list)
    res_list = [os.path.basename(i) for i in res_list]

    restarts_counter = Counter(res_list)

    d = {'restarts': [i for i in restarts_counter if restarts_counter[i] >= prj_count]}

    # print(c)
    #
    #
    # print(f'Количество проектов {prj_count}')
    # print()

    # res_list = glob.glob('./**/restarts/*.rst', recursive=True)
    # name_res_list = set([i.split('\\')[-1] for i in res_list])
    return d
