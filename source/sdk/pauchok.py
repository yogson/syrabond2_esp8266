import ujson as json
import uasyncio
import network
import machine
import ubinascii

from webcreds import run_webcreds_server

CONFIGS = ["global.json", "conf.json", "network.json"]

class SilentObject:
    def __init__(self, instead='Unknown'):
        self.instead = instead

    def __getattr__(self, name):
        def do_nothing(*args, **kwargs):
            return "Nothing"
        return do_nothing

class LED:

    PIN = None
    LEVEL = 0

    def __init__(self):
        self._led = None
        self._blinking = False
        self._blink_task = None

    @property
    def led(self):
        if not self._led and self.PIN:
            self._led = machine.Pin(self.PIN, machine.Pin.OUT)
        return self._led

    def on(self):
        led = self.led
        if led:
            led.value(self.LEVEL)

    def off(self):
        led = self.led
        if led:
            led.value(abs(self.LEVEL - 1))

    async def _blink(self):
        while self._blinking:
            self.on()
            await uasyncio.sleep(0.5)
            self.off()
            await uasyncio.sleep(0.5)

    def start_blinking(self):
        self._blinking = True
        if self._blink_task is None or self._blink_task.done():
            self._blink_task = uasyncio.get_event_loop().create_task(self._blink())

    def stop_blinking(self):
        self._blinking = False
        if self._blink_task and not self._blink_task.done():
            self._blink_task.cancel()
            self._blink_task = None

    def cleanup(self):
        self.stop_blinking()
        self.off()

class WiFiNetworkManager:

    led = LED()
    ssid = None
    password = None

    def __init__(self):
        self.ip = None
        self._task = None

    async def _connect(self):
        self.led.start_blinking()
        sta_if = network.WLAN(network.STA_IF)
        print('Connecting to network', self.ssid, "...")
        sta_if.active(True)
        sta_if.connect(self.ssid, self.password)

        i = 0
        while not sta_if.isconnected():
            await uasyncio.sleep(0.5)
            i += 1
            if i == 19:
                start_ap()
                start_repl()
                await run_webcreds_server()

        netconf = sta_if.ifconfig()
        print('Connected:', netconf)
        self.ip = netconf[0]
        stop_ap()
        self.led.cleanup()

    def connect(self):
        if self._task is None or self._task.done():
            self._task = uasyncio.get_event_loop().create_task(self._connect())

class Pauchok:

    mqtt = None
    network = None

def apply_conf(conf: str):
    try:
        print("Applying config", conf)
        conf_data = json.loads(conf)
        update_conf(conf_data)
    except:
        print("Couldn't update config ", conf)

def update_conf(conf_update: dict):
    conf_file = "conf.json"
    config = get_config(conf_file)
    config.update(conf_update)
    write_config(conf_file, config)

def get_config(*args):
    if not args:
        args = CONFIGS
    confs = []

    for c_file in args:
        try:
            with open(c_file) as f:
                config = json.loads(f.read())
                confs.append(config)
        except (OSError, ValueError):
            print("Couldn't load config ", c_file)
    resulting = {}
    for conf in confs:
        for key in conf:
            if key not in resulting:
                resulting[key] = conf[key]
            else:
                if isinstance(resulting[key], dict):
                    resulting[key].update(conf[key])
    return resulting

def write_config(filename, conf):
    try:
        with open(filename, 'w') as f:
            f.write(json.dumps(conf))
    except (OSError, ValueError):
        print("Couldn't open config ", filename)

def start_repl():
    import webrepl
    webrepl.start()

def start_ap():
    ap_if = network.WLAN(network.AP_IF)
    uid = ubinascii.hexlify(machine.unique_id()).decode()
    ap_if.config(essid=uid)
    ap_if.active(True)
    print('Access point enabled:', uid)
    print(ap_if.ifconfig())

def stop_ap():
    ap_if = network.WLAN(network.AP_IF)
    if ap_if.active():
        ap_if.active(False)