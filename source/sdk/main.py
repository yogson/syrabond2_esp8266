import machine
import uasyncio
import gc

from pauchok import WiFiNetworkManager, Pauchok, get_config
from mqttsender import Mqttsender


async def check_errors(plugins):
    while 1:
        for plugin in plugins:
            if hasattr(plugin, "errors"):
                if plugin.errors > 9:
                    machine.reset()
        await uasyncio.sleep(60)


config = get_config()
mqtt = config.get('mqtt')
plugin_configs = config.get('plugins')
debug = config.get('debug')

Pauchok.mqtt = Mqttsender(mqtt)
Pauchok.network = WiFiNetworkManager()


del mqtt
plugins = {}
gc.collect()
for plugin_conf in plugin_configs:
    module = __import__(plugin_conf.get('module'))
    print(plugin_conf)
    plugin_inst = module.Plugin(**plugin_conf)
    plugins.update({plugin_conf.get('module'): plugin_inst})

loop = uasyncio.get_event_loop()

Pauchok.network.connect()
loop.create_task(Pauchok.mqtt.heartbit())

if not debug:
    for name, plugin in plugins.items():
        print("Running plugin", name)
        loop.create_task(plugin.run())
    loop.create_task(check_errors(plugins.values()))

try:
    loop.run_forever()
except Exception as e:
    print(e)
