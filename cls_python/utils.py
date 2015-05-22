__author__ = 'Amry Fitra'

import decorator
import time
import threading

def retry(howmany, *exception_types, **kwargs):
    timeout = kwargs.get('timeout', 0.0) # seconds

    @decorator.decorator
    def try_it(func, *fargs, **fkwargs):
        for _ in range(howmany):
            try: return func(*fargs, **fkwargs)
            except exception_types or Exception:
                if timeout is not None:
                    time.sleep(timeout)
    return try_it

class PeriodicTask(object):
    def __init__(self, interval, callback, daemon=True, **kwargs):
        self.interval = interval
        self.callback = callback
        self.daemon = daemon
        self.kwargs = kwargs

    def run(self):
        self.callback(**self.kwargs)
        t = threading.Timer(self.interval, self.run)
        t.daemon = self.daemon
        t.start()