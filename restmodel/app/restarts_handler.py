import asyncio
from watchgod import awatch
import glob
import time
import shutil
import os

dir_list = glob.glob('./**/restarts', recursive=True)
script_dir = os.path.dirname(__file__)

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

async def watch_restarts(model_name):
    tasks = [asyncio.ensure_future(watch(model_name, i)) for i in dir_list]
    await asyncio.wait(tasks)

def clear_temp_restarts():
    dir_list = glob.glob('./**/temp_restarts', recursive=True)
    for folder in dir_list:
        shutil.rmtree(os.path.abspath(folder))
