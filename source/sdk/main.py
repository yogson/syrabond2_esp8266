import machine
from time import sleep
import uasyncio

from base import plugins, CONFIG_MAP


async def check_errors(plugins: list):
    while 1:
        for plugin in plugins:
            if hasattr(plugin, "errors"):
                if plugin.errors > 9:
                    machine.reset()
        await uasyncio.sleep(60)

loop = uasyncio.get_event_loop()
loop.create_task(CONFIG_MAP["mqtt"].heartbit())

if not CONFIG_MAP["debug"]:

    for name, plugin in plugins.items():
        print("Running plugin", name)
        loop.create_task(plugin.run())
    loop.create_task(check_errors(plugins.values()))
    try:
        loop.run_forever()
    finally:
        sleep(30)
        machine.reset()
