import ubinascii
import network
import machine

import pauchok


sta_if = network.WLAN(network.STA_IF)
netconf = 0
while not netconf:
    if sta_if.isconnected():
        netconf = sta_if.ifconfig()
ip = netconf[0]

config = pauchok.get_config('global.json', 'conf.json')
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
topic = mqtt.get('object', 'myHome') + '/' + mqtt.get('channel', 'resource') + '/' + uid
mqttsender.send(mqttsender.topic_lastwill, str(
    {'uid': uid, 'channel': mqtt.get('channel', 'resource'), "ip": ip, 'topic': topic}), retain=False)

del mqtt

plugins = {}

for plugin_conf in plugin_configs:
    module = __import__(plugin_conf.get('module'))
    plugin_inst = module.Plugin(**plugin_conf)
    plugins.update(
        {plugin_conf.get('module'): plugin_inst}
    )
