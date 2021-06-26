# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import threading
from django.db import connection


class ThreadPool():

    def __init__(self, processes=20):
        self.processes = processes
        self.threads = [PersistentThread() for _ in range(0, processes)]

    def get_dead_threads(self):
        dead = []
        for thread in self.threads:
            if not thread.is_alive():
                dead.append(thread)
        return dead

    def is_thread_running(self):
        return len(self.get_dead_threads()) < self.processes

    def map(self, func, values):
        attempted_count = 0
        values_iter = iter(values)
        # loop until all values have been attempted to be processed and
        # all threads are finished running
        while (attempted_count < len(values) or self.is_thread_running()):
            for thread in self.get_dead_threads():
                try:
                    # run thread with the next value
                    value = next(values_iter)
                    attempted_count += 1
                    thread.run(func, value)
                except StopIteration:
                    break

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass


class PersistentThread():

    def __init__(self):
        self.thread = None

    def run(self, target, *args, **kwargs):
        self.thread = JobThread(target=target,
                                args=args,
                                kwargs=kwargs)
        self.thread.start()

    def is_alive(self):
        if self.thread:
            return self.thread.is_alive()
        else:
            return False

class JobThread(threading.Thread):

    def run(self):
        super().run()
        # explicity close db connection to avoid idle connections
        connection.close()
