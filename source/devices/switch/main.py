import machine
import uasyncio

from base import mqttsender, debug, plugins, loop


async def main():
    if 'switch' in plugins:
        plugins['switch'].set_broker(mqttsender, plugins['switch'].topic)
        if not debug:
            try:
                while True:
                    plugins['switch'].update_site()
                    print('Waiting for message in topic %s...' % plugins['switch'].topic)
                    mqttsender.c.check_msg()
                    await uasyncio.sleep(1)
            finally:
                machine.reset()

loop.create_task(main())

