import machine
from time import sleep

from base import plugins, CONFIG_MAP


if not CONFIG_MAP["debug"]:

    for name, plugin in plugins.items():
        print("Running plugin", name)
        try:
            plugin.run()
        finally:
            sleep(30)
            machine.reset()
