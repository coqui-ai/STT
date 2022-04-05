#!/usr/bin/env python
import multiprocessing
import multiprocessing.pool
import os
import sys
from contextlib import contextmanager


def target_fn(*args, **kwargs):
    return target_impl.run(*args, **kwargs)


def target_fn_single(arg):
    return target_impl.run(arg)


def init_fn(target_impl_cls, global_lock, parent_env, id_queue, initargs):
    process_id = id_queue.get()

    global target_impl
    target_impl = target_impl_cls()
    target_impl._child_init(global_lock, process_id)

    child_env = target_impl.get_child_env(parent_env)
    if child_env is not None:
        os.environ = child_env

    target_impl.init(*initargs)


class PoolBase:
    """Object oriented wrapper around multiprocessing.pool.Pool.

    Users should subclass this class and implement the `run` method, and
    optionally the `init` method.

    `init` will be called, in the child process, once per process. In your
    implementation you can use `self.lock` which is a lock object shared accross
    all child processes in order to synchronize work between all processes. You
    can also use `self.process_id`, which is an integer, unique per process,
    increasing in value from 0 to processes-1 (if not specified, processes
    defaults to os.cpu_count()).

    `run` will be called, in the child processes, potentially multiple times, in
    order to process data.

    You can then use the `create` classmethod to create a new Pool object, which
    can then be used with the usual multiprocessing.pool.Pool methods (eg. map,
    imap, imap_unordered, etc).

    Example usage:

        class MultiplyByTwoPool(PoolBase):
            def init(self, pool_name):
                with self.lock:
                    print(f"[{pool_name}] synchronized step in proc {self.process_id}")

            def get_child_env(self, parent_env):
                parent_env["TEST_VAR"] = str(self.process_id)
                return parent_env

            def run(self, x):
                assert os.environ["TEST_VAR"] == str(self.process_id)
                return x*2

        pool = MultiplyByTwoPool.create(processes=4, initargs=("my pool",))
        print(pool.map(range(10)))
    """

    @classmethod
    def create_impl(cls, processes=None, context=None, initargs=(), *args, **kwargs):
        if processes is None:
            processes = os.cpu_count()

        if context is None:
            context = multiprocessing

        queue = context.Queue()
        for i in range(processes):
            queue.put(i)

        lock = context.Lock()
        parent_env = os.environ.copy()
        pool = cls()
        pool._inner_pool = multiprocessing.pool.Pool(
            processes=processes,
            initializer=init_fn,
            initargs=(cls, lock, parent_env, queue, initargs),
            context=context,
            *args,
            **kwargs,
        )

        return pool

    @classmethod
    @contextmanager
    def create(cls, processes=None, context=None, initargs=(), *args, **kwargs):
        pool = cls.create_impl(processes, context, initargs, *args, **kwargs)
        try:
            yield pool
        finally:
            pool._inner_pool.close()

    def _child_init(self, lock, process_id):
        self.lock = lock
        self.process_id = process_id

    def init(self, *args):
        pass

    def run(self, *args, **kwargs):
        raise NotImplementedError()

    def get_child_env(self, parent_env):
        return None

    def apply(self, *args, **kwargs):
        return self._inner_pool.apply(target_fn, *args, **kwargs)

    def apply_async(self, *args, **kwargs):
        return self._inner_pool.apply_async(target_fn, *args, **kwargs)

    def map(self, *args, **kwargs):
        return self._inner_pool.map(target_fn, *args, **kwargs)

    def map_async(self, *args, **kwargs):
        return self._inner_pool.map_async(target_fn, *args, **kwargs)

    def imap(self, *args, **kwargs):
        return self._inner_pool.imap(target_fn, *args, **kwargs)

    def imap_unordered(self, *args, **kwargs):
        return self._inner_pool.imap_unordered(target_fn, *args, **kwargs)

    def starmap(self, *args, **kwargs):
        return self._inner_pool.starmap(target_fn, *args, **kwargs)

    def starmap_async(self, *args, **kwargs):
        return self._inner_pool.starmap_async(target_fn, *args, **kwargs)

    def close(self):
        return self._inner_pool.close()

    def terminate(self):
        return self._inner_pool.terminate()

    def join(self):
        return self._inner_pool.join()


if __name__ == "__main__":

    class MultiplyByTwoPool(PoolBase):
        def init(self):
            with self.lock:
                print(f"synchronized step in proc {self.process_id}")

        def get_child_env(self, parent_env):
            parent_env["TEST_VAR"] = str(self.process_id)
            return parent_env

        def run(self, x):
            assert os.environ["TEST_VAR"] == str(self.process_id)
            return x * 2

    pool = MultiplyByTwoPool.create(processes=4)
    print(pool.apply((2,)))
    print(pool.map(range(10)))
