class SerialConfig:

    def __init__(self, **kwargs):
        args = ['name', 'device', 'baudrate', 'timeout', 'write_timeout']
        checks = [lambda n: type(n) is str,
                  lambda d: type(d) is str,
                  lambda b: type(b) is int,
                  lambda t: type(t) is float,
                  lambda t: type(t) is float,
                  lambda e: type(e) is bool]

        for f_idx, a in enumerate(args):
            if not kwargs[a]:
                raise ValueError(f'{a} arg missing')

            if not checks[ f_idx ](kwargs[a]):
                raise ValueError(f'{a} is of incorrect type')

        self.name = kwargs['name']
        self.device = kwargs['device']
        self.baudrate = kwargs['baudrate']
        self.timeout = kwargs['timeout']
        self.write_timeout = kwargs['write_timeout']
        self.fallback = kwargs['fallback']