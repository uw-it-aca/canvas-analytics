import queue
import threading
from multiprocessing import Queue


class ThreadPool():

    def __init__(self, processes=20):
        self.processes = processes
        self.threads = [Thread() for _ in range(0, processes)]
        self.mp_queue = Queue()

    def yield_dead_threads(self):
        for thread in self.threads:
            if not thread.is_alive():
                yield thread

    def map(self, func, values):
        completed_count = 0
        values_iter = iter(values)
        while completed_count < len(values):
            try:
                self.mp_queue.get_nowait()
                completed_count += 1
            except queue.Empty:
                pass
            for thread in self.yield_dead_threads():
                try:
                    # run thread with the next value
                    value = next(values_iter)
                    thread.run(func, value, self.mp_queue)
                except StopIteration:
                    break

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass


class Thread():

    def __init__(self):
        self.thread = None

    def run(self, target, *args, **kwargs):
        self.thread = threading.Thread(target=target,
                                       args=args,
                                       kwargs=kwargs)
        self.thread.start()

    def is_alive(self):
        if self.thread:
            return self.thread.is_alive()
        else:
            return False
