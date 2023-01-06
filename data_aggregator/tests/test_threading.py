# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import queue
import unittest
from django.test import TestCase
from multiprocessing import Queue
from data_aggregator.threads import ThreadPool, PersistentThread
from mock import MagicMock


class TestThreadPool(TestCase):

    test_queue = Queue()

    def _get_processed_values(self, num_processed_values):
        processed_values = []
        while len(processed_values) < num_processed_values:
            try:
                processed_values.append(
                    TestThreadPool.test_queue.get_nowait()
                )
            except queue.Empty:
                continue
        return processed_values

    def run_job(self, value):
        value += 1
        TestThreadPool.test_queue.put_nowait(value)

    def test_map(self):
        # as context manager
        with ThreadPool(processes=2) as pool:
            pool.map(self.run_job, [1, 2, 3, 4, 5])
            self.assertEqual(len(pool.threads), 2)
        # read all processed values
        processed_values = self._get_processed_values(5)
        # assert that values were processed
        self.assertEqual([2, 3, 4, 5, 6],
                         sorted(processed_values))

        # as normal class instance
        pool = ThreadPool(processes=3)
        self.assertEqual(len(pool.threads), 3)
        pool.map(self.run_job, [3, 2, 4, 2, 1])
        # read all processed values
        processed_values = self._get_processed_values(5)
        # assert that values were processed
        self.assertEqual([2, 3, 3, 4, 5],
                         sorted(processed_values))

        # test where there are less values than the thread pool size
        pool = ThreadPool(processes=20)
        self.assertEqual(len(pool.threads), 20)
        pool.map(self.run_job, [9, 4, 3, 1, 1])
        # read all processed values
        processed_values = self._get_processed_values(5)
        # assert that values were processed
        self.assertEqual([2, 2, 4, 5, 10],
                         sorted(processed_values))

        # test where job raises an uncaught exception
        bad_job = MagicMock()
        pool = ThreadPool(processes=2)
        self.assertEqual(pool.processes, 2)
        self.assertEqual(len(pool.threads), 2)
        pool.get_dead_threads = MagicMock()
        t1 = PersistentThread()
        self.assertEqual(t1.is_alive(), False)
        t2 = PersistentThread()
        self.assertEqual(t2.is_alive(), False)
        pool.get_dead_threads.return_value = [t1, t2]
        pool.map(bad_job, [9, 4, 3, 1, 1])


if __name__ == "__main__":
    unittest.main()
