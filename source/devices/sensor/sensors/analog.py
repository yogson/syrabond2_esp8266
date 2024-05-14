import machine

from base_sensor import BaseSensor


class Plugin(BaseSensor):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.channel = kwargs.get("value_name", 'readings')
        self.sensor = machine.ADC(0)

    def do(self,  *args, **kwargs):
        return {self.channel: str(self.sensor.read())}


