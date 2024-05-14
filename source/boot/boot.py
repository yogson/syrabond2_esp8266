import gc
from uos import urandom as rnd
from time import sleep

from pauchok import LED, WiFiNetworkManager, get_config, start_ap, start_repl, CONFIGS


config = get_config(*CONFIGS)

if not config:
    print("Couldn't load any config")
    start_ap()
    start_repl()

if config.get("wait", False) is True:
    t = int.from_bytes(rnd(1), 'little') // 25 + 1
    print('Waiting ' + str(t) + ' sec.')  # wait randomized time to balance the load
    sleep(t)

if config.get('led') is not None:
    LED.PIN = int(config['led'])

if config.get("ssid") and config.get("pass") and not config.get("network"):
    config["network"] = {}
    config["network"]["ssid"] = config.pop("ssid")
    config["network"]["pass"] = config.pop("pass")

WiFiNetworkManager.ssid = config.get("network", {}).get("ssid")
WiFiNetworkManager.password = config.get("network", {}).get("pass")

if config.get('repl', True):
    start_repl()

LED().on()
sleep(0.1)
LED().off()

gc.collect()