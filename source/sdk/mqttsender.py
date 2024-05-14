import uasyncio
import ubinascii
import machine
from time import sleep
from umqtt.simple import MQTTClient
import ujson as json

from pauchok import Pauchok, get_config, CONFIGS, apply_conf, write_config, SilentObject


class Mqttsender:

    def __init__(self, mqtt, clean_session=False):
        self.server = mqtt['server']
        self.user = mqtt['user']
        self.password = mqtt['pass']
        self.object = mqtt['object']
        self.uniqid = ubinascii.hexlify(machine.unique_id()).decode()
        self.topic_lastwill = self.object + '/status/' + self.uniqid
        self.topic_management = self.object + '/management/' + self.uniqid
        self.topic_conf = self.object + '/' + self.uniqid + '/conf'
        self.topic_state = self.object + '/state/' + self.uniqid
        self.keepalive = int(mqtt['keepalive'])
        self.clean_session = clean_session
        self.connected = False
        self._c = None
        self.message_queue = {}
        self._async_connect_task = None

        # ------- management commands ----------
        # TODO dehardcode maintenance topics and keywords!
        self._cmd_ping = 'PING'
        self.repl_on = 'ZAVULON'
        self.repl_off = 'ISAAK'
        self.reboot = 'ZARATUSTRA'
        self.get_state = 'STATE'
        self.init = 'INITIALIZE'

    @property
    def c(self):
        if not self._c:
            self._c = MQTTClient(
                self.uniqid, server=self.server, user=self.user, password=self.password, keepalive=self.keepalive)
            self._c.set_callback(self.callback)
            if self.keepalive:
                self._c.set_last_will(topic=self.topic_lastwill, msg='offline', retain=True)
        if not self.connected and Pauchok.network.ip:
            if self._async_connect_task is None or self._async_connect_task.done():
                self._async_connect_task = uasyncio.get_event_loop().create_task(self._connect(self._c))
        for _ in range(5):
            if not self.connected:
                sleep(0.2)
        if not self.connected:
            return SilentObject(instead="MQTT sender")
        return self._c

    async def _connect(self, broker: MQTTClient):
        while not self.connected:
            try:
                self.connected = broker.connect(clean_session=self.clean_session)
                print('Broker at ' + self.server + ' connected')
                self.send_ip()
            except Exception as e:
                print('Connecting error: ', e)
                await uasyncio.sleep(1)
        self.management_subscribe()

    def management_subscribe(self):
        try:
            self.subscribe(self.topic_management)
            self.subscribe(self.topic_conf)
            return False
        except Exception as e:
            print(e)
            return True

    def callback(self, topic, msg):
        topic = topic.decode()
        print("Pauchok got new message in", topic)
        if topic in (self.topic_management, self.topic_conf):
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
        self.send(self.topic_lastwill, str({"ip": Pauchok.network.ip, "uid": self.uniqid}), retain=False)

    def send_config(self):
        config = get_config(*CONFIGS)
        self.send(self.topic_lastwill, json.dumps(config), retain=False)

    def manage(self, topic, command):
        print('Maintenance command received:', topic)
        if command == self.repl_on:
            import webrepl
            webrepl.start()
        elif command == self.repl_off:
            import webrepl
            webrepl.stop()
        elif command == self.reboot:
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
            self.c.check_msg()

    def ping_broker(self):
        self.c.ping()

    async def heartbit(self):
        while True:
            self.ping_broker()
            await uasyncio.sleep(self.keepalive // 3)