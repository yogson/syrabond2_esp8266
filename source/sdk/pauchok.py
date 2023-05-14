from umqtt.simple import MQTTClient
import ujson as json
from time import sleep
import uasyncio

from const import CONFIGS


class Mqttsender:

    def __init__(self, mqtt, ip, uniqid, clean_session=False):
        self.server = mqtt['server']
        self.user = mqtt['user']
        self.password = mqtt['pass']
        self.uniqid = uniqid
        self.topic_ping = mqtt['object'] + '/globalping'
        self.topic_lastwill = mqtt['object'] + '/status/' + self.uniqid
        self.topic_management = mqtt['object'] + '/management/' + self.uniqid
        self.topic_conf = mqtt['object'] + '/' + self.uniqid + '/conf'
        self.topic_state = mqtt['object'] + '/state/' + self.uniqid
        self.keepalive = int(mqtt['keepalive'])
        self.ip = ip
        self.clean_session = clean_session
        self.connected = False
        self.c = MQTTClient(self.uniqid, server=self.server, user=self.user, password=self.password,
                            keepalive=self.keepalive)
        self.c.set_callback(self.callback)
        if self.keepalive:
            self.c.set_last_will(topic=self.topic_lastwill, msg='offline', retain=True)
        self.message_queue = {}

        # ------- management commands ----------
        # TODO dehardcode maintenance topics and keywords!
        self._cmd_ping = 'PING'
        self.repl_on = 'ZAVULON'
        self.repl_off = 'ISAAK'
        self.reboot = 'ZARATUSTRA'
        self.get_state = 'STATE'
        self.init = 'INITIALIZE'

    def _connect(self):
        while not self.connected:
            try:
                print('Connecting as ', self.uniqid, '...')
                self.connected = self.c.connect(clean_session=self.clean_session)
                print('Broker at ' + self.server + ' connected')
            except Exception as e:
                print('Connecting error: ', e)
                sleep(5)

    def connect(self):
        self._connect()
        self.management_subscribe()

    def management_subscribe(self):
        print('Subscribing maintenance topics...')
        try:
            self.subscribe(self.topic_ping)
            self.subscribe(self.topic_management)
            self.subscribe(self.topic_conf)
            return False
        except Exception as e:
            print("Could not subscribe")
            print(e)
            return True

    def callback(self, topic, msg):
        topic = topic.decode()
        print("Pauchok got new message in", topic)
        if topic in (self.topic_ping, self.topic_management, self.topic_conf):
            return self.manage(topic, msg.decode())
        if topic in self.message_queue:
            return self.message_queue[topic].get("callback")(topic, msg)

        topic_parts = topic.split("/")
        for i in reversed(range(1, len(topic_parts))):
            wildcard_topic = "/".join(topic_parts[:i]) + "/#"
            if wildcard_topic in self.message_queue:
                return self.message_queue[wildcard_topic].get("callback")(topic, msg)

        print("Message unhandled: ", msg.decode())

    def send(self, topic, message, retain=True):
        is_error = False
        print('Sending ' + str(message) + ' in topic ' + str(topic) + '...')

        try:
            if not isinstance(topic, bytes):
                topic = topic.encode()
            if not isinstance(message, bytes):
                message = message.encode()
            self.c.publish(topic, message, retain=retain)
            print('Data sent')

        except Exception as e:
            print("Could not send data")
            print(e)
            is_error = True
        finally:
            return is_error

    def subscribe(self, topic, sub_cb=None):
        if sub_cb:
            if topic not in self.message_queue:
                self.message_queue[topic] = {
                    'callback': sub_cb,
                    'messages': []
                }
            else:
                self.message_queue[topic]['callback'] = sub_cb
        self.c.subscribe(topic.encode())
        print('Subscribed: ' + topic)

    def send_ip(self):
        self.send(self.topic_lastwill, str({"ip": self.ip}), retain=False)

    def send_config(self):
        config = get_config(*CONFIGS)
        self.send(self.topic_lastwill, json.dumps(config), retain=False)

    def manage(self, topic, command):
        print('Maintenance command received:', topic)
        if command == self._cmd_ping:
            self.send_ip()
        elif command == self.repl_on:
            import webrepl
            webrepl.start()
        elif command == self.repl_off:
            print('Turning repl off')
            import webrepl
            webrepl.stop()
        elif command == self.reboot:
            print('Rebooting...')
            import machine as m
            m.reset()
        elif command == self.init:
            conf = get_config('conf.json')
            conf['inited'] = '1'
            write_config('conf.json', conf)
        elif command == self.get_state:
            self.send_config()
        elif topic == self.topic_conf:
            apply_conf(command)

    def check_msg(self):
        try:
            self.c.check_msg()
        except OSError:
            self.connected = False
            self._connect()
            self.c.check_msg()

    def ping_broker(self):
        self.c.ping()

    async def heartbit(self):
        while True:
            self.ping_broker()
            await uasyncio.sleep(self.keepalive // 4)


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
