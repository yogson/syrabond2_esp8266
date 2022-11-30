import machine


class Plugin:

    def __init__(self, **kwargs):
        self.channel = kwargs.get("channel_name", 'readings')
        self.sensor = machine.ADC(0)

    def do(self,  *args, **kwargs):
        return {self.channel: str(self.sensor.read())}
