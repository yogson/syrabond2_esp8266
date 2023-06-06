import machine

from base import BaseSensor


class Plugin(BaseSensor):

    def __init__(self, *, config_map, **kwargs):
        super().__init__(config_map=config_map, **kwargs)
        self.channel = kwargs.get("value_name", 'readings')
        self.sensor = machine.ADC(0)

    def do(self,  *args, **kwargs):
        return {self.channel: str(self.sensor.read())}

    async def run(self):
        while 1:
            self.check_messages()

