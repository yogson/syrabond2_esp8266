import machine
from time import sleep
import uasyncio

from base import plugins, CONFIG_MAP

loop = uasyncio.get_event_loop()


if not CONFIG_MAP["debug"]:

    for name, plugin in plugins.items():
        print("Running plugin", name)
        try:
            loop.create_task(CONFIG_MAP["mqtt"].heartbit())
            loop.create_task(plugin.run())
            loop.run_forever()
        finally:
            sleep(30)
            machine.reset()
