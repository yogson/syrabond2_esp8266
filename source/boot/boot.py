import machine
import ubinascii
import gc
from uos import urandom as rnd
import network
from time import sleep

import sdk.pauchok as pauchok


def start_repl():
    import webrepl
    webrepl.start()


def start_management_interface():
    ap_if = network.WLAN(network.AP_IF)
    sta = network.WLAN(network.STA_IF)
    uid = ubinascii.hexlify(machine.unique_id()).decode()
    ap_if.active(True)
    ap_if.config(essid=uid)
    print(ap_if.ifconfig())
    print('AP uid:', uid)
    start_repl()
    import webcreds
    serv = webcreds.Http()
    conn_flag = 0
    if serv:
        while not sta.isconnected():
            serv.get_request()
            if serv.raw_requestline:
                conn_flag = 1
                serv.parse_request()
                serv.handle_request()
            if conn_flag:
                if led:
                    led.value(OFF)
                sleep(0.1)
                if led:
                    led.value(ON)
            else:
                if led:
                    led.value(OFF)
                sleep(1.5)
                if led:
                    led.value(ON)
                sleep(0.5)


def connect(ssid, password):
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    if not sta_if.isconnected():
        print('Connecting to network...', ssid, password)
        sta_if.active(True)
        sta_if.connect(ssid, password)
        t = 0
        while not sta_if.isconnected():
            if t < 60:
                if led:
                    led.value(OFF)
                sleep(0.5)
                if led:
                    led.value(ON)
                sleep(0.5)
                t += 1

            else:
                if not ap_if.active():
                    print('Could not connect to network. Setting up soft AP and keep trying...')
                    start_management_interface()

    print('Connected:', sta_if.ifconfig())
    ap_if.active(False)
    if led:
        led.value(ON)


t = int.from_bytes(rnd(1), 'little') // 25 + 1
print('Waiting ' + str(t) + ' sec.')  # wait randomized time to balance the load
sleep(t)

led = None
config = pauchok.get_config("global.json", "conf.json", "network.json")

if not config:
    print("Couldn't load any config")
    start_management_interface()
    machine.reset()

if config.get('led') is not None:
    led = machine.Pin(int(config['led']), machine.Pin.OUT)
    level = int(config.get('level', 0))
    ON = int(level)
    OFF = abs(ON - 1)
    led.value(OFF)

if config.get("ssid") and config.get("pass") and not config.get("network"):
    config["network"]["ssid"] = config.pop("ssid")
    config["network"]["pass"] = config.pop("pass")

connect(config.get("network", {}).get("ssid", "wifi"), config.get("network", {}).get("pass", ""))

if config.get('repl'):
    print('starting webrepl cuz configured...')
    start_repl()

gc.collect()

if led:
    led.value(ON)
