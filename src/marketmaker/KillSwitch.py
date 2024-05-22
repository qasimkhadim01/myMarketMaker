import asyncio
import logging

import Static

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
Static.appLoggers.append(logger)

class KillSwitch:
    def __init__(self, loop):
        self.loop = loop

    async def run(self):
        while True:
            await asyncio.sleep(30)
            if self.isKill():
                break
        Static.KeepRunning = False

        tasks = [t for t in asyncio.all_tasks()]
        for t in tasks:
            t.cancel()

        self.loop.stop()
        asyncio.current_task().cancel()

    def isKill(self):
        if Static.Kill: return True
