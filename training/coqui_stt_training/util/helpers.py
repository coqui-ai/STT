import heapq
import os
import random
import sys
import time
from collections import namedtuple
from multiprocessing import Pool

import semver

KILO = 1024
KILOBYTE = 1 * KILO
MEGABYTE = KILO * KILOBYTE
GIGABYTE = KILO * MEGABYTE
TERABYTE = KILO * GIGABYTE
SIZE_PREFIX_LOOKUP = {"k": KILOBYTE, "m": MEGABYTE, "g": GIGABYTE, "t": TERABYTE}

ValueRange = namedtuple("ValueRange", "start end r")


def parse_file_size(file_size):
    if type(file_size) is str:
        file_size = file_size.lower().strip()
        if len(file_size) == 0:
            return 0
        n = int(keep_only_digits(file_size))
        if file_size[-1] == "b":
            file_size = file_size[:-1]
        e = file_size[-1]
        return SIZE_PREFIX_LOOKUP[e] * n if e in SIZE_PREFIX_LOOKUP else n
    elif type(file_size) is int:
        return file_size
    else:
        raise ValueError("file_size not of type 'int' or 'str'")


def keep_only_digits(txt):
    return "".join(filter(str.isdigit, txt))


def secs_to_hours(secs):
    hours, remainder = divmod(secs, 3600)
    minutes, seconds = divmod(remainder, 60)
    return "%d:%02d:%02d" % (hours, minutes, seconds)


def check_ctcdecoder_version():
    ds_version_s = (
        open(os.path.join(os.path.dirname(__file__), "../VERSION")).read().strip()
    )

    try:
        # pylint: disable=import-outside-toplevel
        from coqui_stt_ctcdecoder import __version__ as decoder_version
    except ImportError as e:
        if e.msg.find("__version__") > 0:
            print(
                "Coqui STT version ({ds_version}) requires CTC decoder to expose __version__. "
                "Please upgrade the coqui_stt_ctcdecoder package to version {ds_version}".format(
                    ds_version=ds_version_s
                )
            )
            sys.exit(1)
        raise e

    rv = semver.compare(ds_version_s, decoder_version)
    if rv != 0:
        print(
            "Coqui STT version ({}) and CTC decoder version ({}) do not match. "
            "Please ensure matching versions are in use.".format(
                ds_version_s, decoder_version
            )
        )
        sys.exit(1)

    return rv


class Interleaved:
    """Collection that lazily combines sorted collections in an interleaving fashion.
    During iteration the next smallest element from all the sorted collections is always picked.
    The collections must support iter() and len()."""

    def __init__(self, *iterables, key=lambda obj: obj, reverse=False):
        self.iterables = iterables
        self.key = key
        self.reverse = reverse
        self.len = sum(map(len, iterables))

    def __iter__(self):
        return heapq.merge(*self.iterables, key=self.key, reverse=self.reverse)

    def __len__(self):
        return self.len


class LenMap:
    """
    Wrapper around python map() output object that preserves the original collection length
    by implementing __len__.
    """

    def __init__(self, fn, iterable):
        try:
            self.length = len(iterable)
        except TypeError:
            self.length = None
        self.mapobj = map(fn, iterable)

    def __iter__(self):
        self.mapobj = self.mapobj.__iter__()
        return self

    def __next__(self):
        return self.mapobj.__next__()

    def __getitem__(self, key):
        return self.mapobj.__getitem__(key)

    def __len__(self):
        return self.length


class LimitingPool:
    """Limits unbound ahead-processing of multiprocessing.Pool's imap method
    before items get consumed by the iteration caller.
    This prevents OOM issues in situations where items represent larger memory allocations."""

    def __init__(
        self,
        processes=None,
        initializer=None,
        initargs=None,
        process_ahead=None,
        sleeping_for=0.1,
    ):
        self.process_ahead = os.cpu_count() if process_ahead is None else process_ahead
        self.sleeping_for = sleeping_for
        self.processed = 0
        self.pool = Pool(
            processes=processes, initializer=initializer, initargs=initargs
        )

    def __enter__(self):
        return self

    def _limit(self, it):
        for obj in it:
            while self.processed >= self.process_ahead:
                time.sleep(self.sleeping_for)
            self.processed += 1
            yield obj

    def imap(self, fun, it):
        for obj in self.pool.imap(fun, self._limit(it)):
            self.processed -= 1
            yield obj

    def terminate(self):
        self.pool.terminate()

    def __exit__(self, exc_type, exc_value, traceback):
        self.pool.close()


def get_value_range(value, target_type):
    """
    This function converts all possible supplied values for augmentation
    into the [start,end,r] ValueRange type. The expected inputs are of the form:

    <number>
    <number>~<number>
    <number>:<number>~<number>

    Any "missing" values are filled so that ValueRange always includes [start,end,r].
    """
    if isinstance(value, str):
        if "~" in value:
            parts = value.split("~")
            if len(parts) != 2:
                raise ValueError("Cannot parse value range")
            value = parts[0]
            r = parts[1]
        else:
            r = 0  # if no <r> supplied, use 0
        parts = value.split(":")
        if len(parts) == 1:
            parts.append(parts[0])  # only one <value> given, so double it
        if len(parts) != 2:
            raise ValueError("Cannot parse value range")
        return ValueRange(target_type(parts[0]), target_type(parts[1]), target_type(r))
    if isinstance(value, tuple):
        if len(value) == 2:
            return ValueRange(
                target_type(value[0]), target_type(value[1]), target_type(0)
            )
        if len(value) == 3:
            return ValueRange(
                target_type(value[0]), target_type(value[1]), target_type(value[2])
            )
        else:
            raise ValueError("Cannot convert to ValueRange: Wrong tuple size")
    if isinstance(value, int) or isinstance(value, float):
        return ValueRange(target_type(value), target_type(value), target_type(0))
    raise ValueError("Cannot convert to ValueRange: Wrong tuple size")


def int_range(value):
    return get_value_range(value, int)


def float_range(value):
    return get_value_range(value, float)


def pick_value_from_range(value_range, clock=None):
    clock = random.random() if clock is None else max(0.0, min(1.0, float(clock)))
    value = value_range.start + clock * (value_range.end - value_range.start)
    value = random.uniform(value - value_range.r, value + value_range.r)
    return round(value) if isinstance(value_range.start, int) else value


def tf_pick_value_from_range(value_range, clock=None, double_precision=False):
    import tensorflow as tf  # pylint: disable=import-outside-toplevel

    if clock is None:
        clock = tf.random.stateless_uniform([], seed=(-1, 1), dtype=tf.float64)
    else:
        clock = tf.maximum(
            tf.constant(0.0, dtype=tf.float64),
            tf.minimum(tf.constant(1.0, dtype=tf.float64), clock),
        )
    value = value_range.start + clock * (value_range.end - value_range.start)
    # sample the value from a uniform distribution with "radius" <r>
    value = tf.random.stateless_uniform(
        [],
        minval=value - value_range.r,
        maxval=value + value_range.r,
        seed=(clock * tf.int32.min, clock * tf.int32.max),
        dtype=tf.float64,
    )
    if isinstance(value_range.start, int):
        return tf.cast(tf.math.round(value), tf.int64 if double_precision else tf.int32)
    return tf.cast(value, tf.float64 if double_precision else tf.float32)
