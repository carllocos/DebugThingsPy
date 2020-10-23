from . import template


def get_config():
    c = {
        'name': 'ttyUSB0',
        'device': '/dev/ttyUSB0',
        'baudrate': 115200,
        'timeout': float(5),
        'write_timeout': float(5),
        'exclusive': True
    }

    return template.Config(**c)
