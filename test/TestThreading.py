import asyncio

class TestCondition():
    def __init__(self, event):
        self.event = event

    async def callback(self):
        while True:
            self.event.set()
            print('Callback notified')
            await asyncio.sleep(2)
            print('Callback sleep done')


    async def run(self):
        while True:
            await self.event.wait()
            print('resumed in run')
            self.event.clear()


class TestEvent():
    def __init__(self, event1, event2):
        self.event1 = event1
        self.event2 = event2

    async def callback(self):
        while True:
            await asyncio.sleep(1)
            self.event1.set()
            print('Callback notified')
            await self.event2.wait()


    async def run(self):
        while True:
            await self.event1.wait()
            print('done')
            await asyncio.sleep(1)
            self.event2.set()

async def myAsync():
    print('test')

def callAsynchFromSync():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(myAsync())
    #retval = [lambda x: asyncio.get_event_loop().run_until_complete(self.exchangeManager.sendLimitOrder(order)) for

test = TestCondition(asyncio.Event())
#test = TestEvent(asyncio.Event(), asyncio.Event())

loop = asyncio.get_event_loop()
loop.create_task(test.run())
loop.create_task(test.callback())



loop.run_forever()
