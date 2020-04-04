import unittest
from src import utils


class TestUtils(unittest.TestCase):
    def test_read_needs_from_csv(self):
        needs_by_day_1, shifts_1 = utils.read_needs_from_csv("test/needs_file.csv", row_index=3, column_index=0)
        expected_shifts_1 = {'M': 0, 'J': 1, 'S': 2, 'N': 3}
        self.assertEqual(shifts_1, expected_shifts_1)
        self.assertTrue(len(needs_by_day_1) == 7)
        self.assertTrue(len(needs_by_day_1[0]) == 4)
        self.assertTrue(type(needs_by_day_1[0]['J']) == int)
        needs_by_day_2, shifts_2 = utils.read_needs_from_csv("test/needs_file.csv", row_index=8, column_index=8)
        self.assertTrue(len(needs_by_day_2) == 7)
        self.assertTrue(len(needs_by_day_2[0]) == 7)
        self.assertTrue(type(needs_by_day_2[0]['M']) == int)


if __name__ == '__main__':
    unittest.main()
