import asyncio
from watchgod import awatch

async def watch():
   async for changes in awatch('.'):
       print(changes)
