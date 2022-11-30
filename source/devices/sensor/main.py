import machine
import gc
from time import sleep

from sdk.base import mqttsender, debug, period, led, plugins, topic, interval


def weighty_diff(one, two, percentage=1):
    try:
        one = float(one)
        two = float(two)
        return abs((one - two) / one * 100) > percentage
    except Exception as e:
        print(e)
        return False


def send_data(top, data):
    for ch in data:
        mqttsender.send(
            top + ch,
            data[ch]
        )


if not debug:
    n = period
    error_counter = 0
    max_error = 10
    readings_wh = {}

    try:
        while 1:
            for i in range(10):
                mqttsender.c.check_msg()
            if error_counter > 0:
                print('Errors to reboot: ', max_error - error_counter)
                if error_counter > max_error:
                    print('Rebooting...')
                    machine.reset()
            led.value(abs(led.value() - 1)) if led else None

            for plugin, instance in plugins.items():
                print(plugin)
                full_topic = topic + '/' + plugin + '/' if len(plugins) > 1 else topic + '/'
                try:
                    # call plugin passing message queue generator as arg
                    reading = instance.do(mqttsender.message_queue)
                    if not reading:
                        error_counter += 1
                        continue
                    if n == period:
                        send_data(full_topic, reading)
                    else:
                        if plugin in readings_wh:
                            for channel in reading:
                                if weighty_diff(readings_wh.get(plugin, {}).get(channel), reading[channel]):
                                    send_data(full_topic, reading)
                                    break

                    readings_wh.update(
                        {plugin: reading}
                    )

                    gc.collect()
                except Exception as e:
                    print('Error:', e)
                    error_counter += 1

            led.value(abs(led.value() - 1)) if led else None
            sleep(interval)
            if n == period:
                n = 0
            n += 1

    finally:
        machine.reset()
