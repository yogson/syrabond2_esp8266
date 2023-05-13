import ubinascii
import network
import machine

import pauchok

from const import CONFIGS

sta_if = network.WLAN(network.STA_IF)
netconf = 0
while not netconf:
    if sta_if.isconnected():
        netconf = sta_if.ifconfig()
ip = netconf[0]

config = pauchok.get_config(*CONFIGS)
mqtt = config.get('mqtt')

plugin_configs = config.get('plugins')

interval = int(config.get("interval", 10))
period = int(config.get("period", 60))
debug = config.get('debug')
inited = config.get('inited')
uid = ubinascii.hexlify(machine.unique_id()).decode()
led = machine.Pin(config.get('led'), machine.Pin.OUT) if config.get('led') else None
led.value(abs(led.value() - 1)) if led else None

mqttsender = pauchok.Mqttsender(mqtt, ip, uid)
mqttsender.connect()
mqttsender.send(mqttsender.topic_lastwill, str({'uid': uid, "ip": ip}), retain=False)

CONFIG_MAP = {
    "object": mqtt.get('object', 'myHome'),
    "mqtt": mqttsender,
    "uid": uid,
    "led": led,
    "ip": ip,
    "debug": debug
}

del mqtt
plugins = {}

for plugin_conf in plugin_configs:
    module = __import__(plugin_conf.get('module'))
    plugin_inst = module.Plugin(**plugin_conf, config_map=CONFIG_MAP)
    plugins.update(
        {plugin_conf.get('module'): plugin_inst}
    )
