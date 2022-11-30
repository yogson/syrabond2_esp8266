import machine
from time import sleep
from si7021 import SI7021


class Plugin:

    def __init__(self, **kwargs):
        scl_pin = kwargs.get('scl_pin')
        sda_pin = kwargs.get('sda_pin')
        self.mismatch_t = kwargs.get('mismatch_t')
        self.mismatch_h = kwargs.get('mismatch_h')
        i2c = machine.I2C(scl=machine.Pin(scl_pin), sda=machine.Pin(sda_pin))
        self.si = SI7021(i2c=i2c)
        self.first_time = True
        
    def do(self, *args, **kwargs):
        try:
            if self.first_time:
                self.si.temperature()
                self.first_time = False
                sleep(5)
            t = stround(self.si.temperature() + self.mismatch_t)
            h = stround(self.si.humidity() + self.mismatch_h)
            return {'temp': t, 'hum': h}
        except Exception as e:
            print(e)
            return {}


def stround(n, c=2):
    if str(n).rfind('.') != -1:
        return str(n)[0:str(n).rfind('.')+c+1]
    else:
        return str(n)