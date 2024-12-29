from machine import Pin
import machine
from time import sleep
from time import ticks_ms
from time import ticks_diff


class Plugin:

    def __init__(self, mqtt, topic=None, **kwargs):
        self.pin = Pin(int(kwargs.get('pin', 12)), Pin.OUT)
        self.led = Pin(int(kwargs.get('led', 13)), Pin.OUT)
        if kwargs.get('button') is not None:
            self.button = Pin(int(kwargs.get('button')), Pin.IN)
            self.button.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.push)
            self.blocking = False
        else:
            self.button = None
        self.change_flag = False
        self.ON = int(kwargs.get('level', 1))
        self.OFF = abs(self.ON-1)
        self.start = 0
        self.mqtt = mqtt
        self.topic = topic or mqtt.object + "/switch/" + mqtt.uniqid
        self.mqtt.subscribe(self.topic, sub_cb=self.callback)
    
    def callback(self, topic, msg):
        print('Got '+msg.decode()+' in '+topic.decode())
        if msg == b"on":
            self.pin.value(self.ON)
            self.led.value(0)
        elif msg == b"off":
            self.pin.value(self.OFF)
            self.led.value(1)

    def push(self, _):
        if self.button.value() == 0:
            self.start = ticks_ms()
            self.blocking = True
        elif self.button.value() == 1:
            if self.blocking:
                if ticks_diff(ticks_ms(), self.start) > 5000:
                    machine.reset()
                print('Switching by button')
                sleep(0.5)
                # self.pin.value(abs(self.pin.value() - 1))
                if self.pin.value() == self.ON:
                    self.pin.value(self.OFF)
                    self.led.value(1)
                elif self.pin.value() == self.OFF:
                    self.pin.value(self.ON)
                    self.led.value(0)
                self.change_flag = True
                self.blocking = False
                sleep(0.5)

    def update_site(self):
        if self.change_flag:
            if self.pin.value() == self.ON:
                self.mqtt.send(self.topic, 'on')
            elif self.pin.value() == self.OFF:
                self.mqtt.send(self.topic, 'off')
            self.change_flag = False


