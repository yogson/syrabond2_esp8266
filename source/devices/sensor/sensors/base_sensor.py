import uasyncio

from pauchok import Pauchok


class BaseSensor:

    def __init__(self, *args, **kwargs):
        self.topic = Pauchok.mqtt.object + "/" + kwargs.get("channel", kwargs.get("module")) + "/" + Pauchok.mqtt.uniqid + "/"
        self.mqtt = Pauchok.mqtt
        self.interval = kwargs.get("interval")
        self.period = kwargs.get("period")
        self.diff_percentage = kwargs.get("percentage", 1)
        self.value = {}
        self.errors = 0

    def do(self):
        raise NotImplementedError

    def check_messages(self):
        for i in range(10):
            self.mqtt.check_msg()

    def send_readings(self, readings: dict):
        for key, value in readings.items():
            self.mqtt.send(self.topic + key, value)

    async def run(self):
        n = self.period
        while 1:
            if not Pauchok.network.ip:
                await uasyncio.sleep(1)
                continue
            self.check_messages()
            try:
                readings: dict = self.do()
                if not readings:
                    self.errors += 1
                    continue
            except:
                self.errors += 1
                continue

            if n == self.period:
                self.send_readings(readings)
            else:
                for channel in readings:
                    if weighty_diff(self.value.get(channel), readings[channel], percentage=self.diff_percentage):
                        self.send_readings(readings)
                        break
            self.value = readings

            await uasyncio.sleep(self.interval)

            if n == self.period:
                n = 0
            n += 1


def weighty_diff(one, two, percentage=1) -> bool:
    if None not in [one, two]:
        one = float(one)
        two = float(two)
        return abs((one - two) / one * 100) > percentage
    return False
