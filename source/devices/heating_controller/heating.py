from machine import Pin
import uasyncio


class Controller:

    def __init__(self, *, config_map, **kwargs):
        self.mqtt = config_map["mqtt"]
        self.protect = kwargs.get("protect_temp")
        self.init_relays(kwargs.get("relays", {}))
        self.relays = []

    def init_relays(self, relays_conf):
        for conf in relays_conf:
            relay = Relay(
                pin=conf.get("pin"),
                name=conf.get("name", "room"),
                hysteresis=conf.get("hysteresis", 0),
                level=conf.get("level", 0),
                t_curr_topic=conf.get("t_curr_topic"),
                t_targ_topic=conf.get("t_targ_topic")
            )
            if self.protect:
                relay.t_target = self.protect
                relay.t_current = 0
            self.relays.append(relay)
            self.mqtt.subscribe(conf.get("t_curr_topic"), self.handle_message)
            self.mqtt.subscribe(conf.get("t_targ_topic"), self.handle_message)

    def handle_message(self, topic, msg):
        for relay in self.relays:
            if topic == relay.t_curr_topic:
                relay.t_current = float(msg.decode())
            elif topic == relay.t_targ_topic:
                relay.t_target = float(msg.decode())

    async def run(self):
        while 1:
            self.mqtt.check_msg()
            for relay in self.relays:
                relay.check()
                await uasyncio.sleep(0.1)
            await uasyncio.sleep(1)


class Relay:

    def __init__(self, pin, name, t_curr_topic, t_targ_topic, hysteresis, level):
        self.pin = Pin(pin, Pin.OUT)
        self.t_curr_topic = t_curr_topic.encode()
        self.t_targ_topic = t_targ_topic.encode()
        self.hysteresis = float(hysteresis)
        self.ON = int(level)
        self.OFF = abs(self.ON - 1)
        self.t_current = 0
        self.t_target = 0
        self.name = name

    def operate(self, act):
        if self.pin.value() != act:
            self.pin.value(act)

    def check(self, mode='heat'):
        print(self.name + ' Current: %.1f Expected: %.1f' % (self.t_current, self.t_target))
        if mode == 'heat':
            if self.t_current < self.t_target:
                self.operate(self.ON)
            else:
                self.operate(self.OFF)
