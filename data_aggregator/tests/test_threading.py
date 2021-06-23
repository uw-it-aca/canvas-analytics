import queue
import unittest
from django.test import TestCase
from multiprocessing import Queue
from data_aggregator.threads import ThreadPool


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

    def run_job(self, value, mp_queue=None):
        value += 1
        if mp_queue is not None:
            mp_queue.put_nowait(value)
            TestThreadPool.test_queue.put_nowait(value)
        return value

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


if __name__ == "__main__":
    unittest.main()
