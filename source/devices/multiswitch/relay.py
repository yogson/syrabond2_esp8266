from machine import Pin
from time import sleep
import uasyncio


class Plugin:

    change_flag = False

    def __init__(self, *, config_map, **kwargs):
        self.topic = config_map["object"] + "/" + kwargs.get("channel", kwargs.get("module")) + "/" + config_map["uid"]
        self.mqtt = config_map["mqtt"]
        Relay.sender = self.mqtt
        self.mqtt.subscribe(self.topic + "/#", self.handle_message)
        self.relays = {}
        self.init_relays(kwargs.get("relays", {}))

    def init_relays(self, relays):
        for rel in relays:
            button = False
            led = False

            if 'button' in rel:
                button = int(rel['button'])

            if 'led' in rel:
                led = int(rel['led'])

            r = Relay(int(rel['pin']), rel['name'], int(rel['level']), button, led)
            r.check(0)
            r.topic = self.topic + '/' + r.name
            self.relays.update({r.topic: r})

    def handle_message(self, topic, msg):
        print("Relay", topic, "got", msg)
        if topic in self.relays:
            if msg == b"on":
                self.relays[topic].check(1)
            elif msg == b"off":
                self.relays[topic].check(0)

    def update_states(self):
        if Plugin.change_flag:
            for relay in self.relays.values():
                if relay.change_flag:
                    relay.update_state()

    async def run(self):
        print('Waiting for message in topic %s...' % self.topic)
        while 1:
            self.update_states()
            self.mqtt.check_msg()
            await uasyncio.sleep(0.1)


class Relay:

    sender = None

    def __init__(self, pin, name, level, button, led=None):
        self.pin = Pin(pin, Pin.OUT)
        if led:
            self.led = Pin(led, Pin.OUT)
        else:
            self.led = None
        if isinstance(button, int):
            self.button = Pin(button, Pin.IN, Pin.PULL_UP)
            self.button.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.push)
        else:
            self.button = False
        self.ON = int(level)
        self.OFF = abs(self.ON-1)
        self.name = name
        self.topic = None
        self.change_flag = False
        self.blocking = False

    def check(self, command):
        if command == 1:
            self.pin.value(self.ON)
            if self.led:
                self.led.value(0)
        elif command == 0:
            self.pin.value(self.OFF)
            if self.led:
                self.led.value(0)

    def push(self, button):
        if self.button.value() == 0:
            self.blocking = True
        elif self.button.value() == 1:
            if self.blocking:
                # self.pin.value(abs(self.pin.value() - 1))
                if self.pin.value() == self.ON:
                    self.pin.value(self.OFF)
                elif self.pin.value() == self.OFF:
                    self.pin.value(self.ON)
                Plugin.change_flag = True
                self.change_flag = True
                sleep(0.5)
                self.blocking = False

    def update_state(self):
        if self.change_flag:
            if self.pin.value() == self.ON:
                self.sender.send(self.topic, 'on')
            elif self.pin.value() == self.OFF:
                self.sender.send(self.topic, 'off')
            self.change_flag = False
