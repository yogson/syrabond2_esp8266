import machine
from time import sleep
import dht

#TODO De-hardcode the names of parameters temp and hum

class Plugin:

    def __init__(self, **config):
        dht_type = config.get('dht_type', 11)
        dht_pin = machine.Pin(config.get('dht_pin', 2), machine.Pin.IN, machine.Pin.PULL_UP)
        self.mismatch_temp = config.get('mismatch_temp', 0)
        self.mismatch_hum = config.get('mismatch_hum', 0)
        if dht_type == 22:
            self.sensor = dht.DHT22(dht_pin)
        else:
            self.sensor = dht.DHT11(dht_pin)
        self.first_time = True

    def do(self, *args):
        if self.first_time:
            try:
                self.first_time = False
                self.sensor.measure()
                sleep(10)
            except:
                sleep(10)
        try:
            self.sensor.measure()
            t = self.sensor.temperature() + self.mismatch_temp
            h = self.sensor.humidity() + self.mismatch_hum
            return {'temp': stround(t), 'hum': stround(h)}
        except Exception as e:
            print(e)
            return "Error"


def stround(n, c=2):
    if str(n).rfind('.') != -1:
        return str(n)[0:str(n).rfind('.')+c+1]
    else:
        return str(n)