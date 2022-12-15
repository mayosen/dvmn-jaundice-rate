from contextlib import contextmanager
from dataclasses import dataclass
import time


@dataclass
class Timer:
    elapsed: float


@contextmanager
def timing():
    timer = Timer(0)
    start = time.monotonic()
    yield timer
    timer.elapsed = time.monotonic() - start
