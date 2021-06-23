import queue
import unittest
from django.test import TestCase
from multiprocessing import Queue
from data_aggregator.threads import ThreadPool


class TestThreadPool(TestCase):

    global_queue = Queue()

    def run_job(self, value, mp_queue=None):
        value += 1
        if mp_queue is not None:
            mp_queue.put_nowait(value)
            TestThreadPool.global_queue.put_nowait(value)
        return value

    def get_processed_values(self):
        processed_values = []
        while True:
            try:
                processed_values.append(
                    TestThreadPool.global_queue.get_nowait()
                )
            except queue.Empty:
                break
        return processed_values

    def test_map(self):
        # as context manager
        with ThreadPool(processes=2) as pool:
            pool.map(self.run_job, [1, 2, 3, 4, 5])
        # read all processed values
        processed_values = self.get_processed_values()
        # assert that values were processed
        self.assertEqual([2, 3, 4, 5, 6],
                         sorted(processed_values))

        # as normal class instance
        pool = ThreadPool(processes=3)
        pool.map(self.run_job, [3, 2, 4, 2, 1])
        # read all processed values
        processed_values = self.get_processed_values()
        # assert that values were processed
        self.assertEqual([2, 3, 3, 4, 5],
                         sorted(processed_values))


if __name__ == "__main__":
    unittest.main()
