import time
from contextlib import contextmanager

@contextmanager
def timer_ms():
    start = time.time()
    yield lambda: int((time.time() - start) * 1000)
