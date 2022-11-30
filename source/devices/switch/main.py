import machine

from sdk.base import mqttsender, debug, plugins, topic


if 'switch' in plugins:

    plugins['switch'].set_broker(mqttsender, topic)

    if not debug:
        try:
            while True:
                plugins['switch'].update_site()
                print('Waiting for message in topic %s...' % plugins['switch'].topic)
                mqttsender.c.wait_msg()

        finally:
            machine.reset()
