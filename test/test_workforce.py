import unittest
from src.utils import read_planning_data_from_csv
from src.workforce import compute_required_workforce_details, compute_required_workforce


class TestWorkforce(unittest.TestCase):
    def test_compute_required_workforce_details(self):
        instance_id, y, bw, annual_h_fix, annual_h_var, pp, p80, t, ratios, costs, av, aff, day_shifts, night_shifts, \
            week_days, week_indices, n, beginning_times, completion_times, durations, break_durations = \
            read_planning_data_from_csv("test/planning_data_file_test.csv")
        fter_day, fter_night, on_fixed_rest_day, on_fixed_rest_night = \
            compute_required_workforce_details(n, day_shifts, night_shifts, durations, break_durations, annual_h_fix,
                                               annual_h_var, week_indices, year=y, include_alsace_moselle=False)
        self.assertTrue(abs(fter_day - 4.55) < 0.01)
        self.assertTrue(abs(fter_night - 5.03) < 0.01)
        self.assertTrue(not on_fixed_rest_day)
        self.assertTrue(not on_fixed_rest_night)

    def test_compute_required_workforce(self):
        instance_id, y, bw, annual_h_fix, annual_h_var, pp, p80, t, ratios, costs, av, aff, day_shifts, night_shifts, \
            week_days, week_indices, n, beginning_times, completion_times, durations, break_durations = \
            read_planning_data_from_csv("test/planning_data_file_test.csv")
        fter = compute_required_workforce(n, day_shifts, night_shifts, durations, break_durations, annual_h_fix,
                                          annual_h_var, week_indices, year=y)
        self.assertTrue(abs(fter - 9.58) < 0.01)


if __name__ == '__main__':
    unittest.main()
