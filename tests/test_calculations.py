"""
test_calculations.py
Unit tests for calculations.py formulas.
"""
import unittest
from src.calculations import (
    vaccinated_initial,
    doses_required,
    cost_before_adj,
    political_multiplier,
    delivery_channel_multiplier,
    newborns,
    second_year_coverage,
    total_cost,
)

class TestCalculations(unittest.TestCase):
    def test_vaccinated_initial(self):
        self.assertEqual(vaccinated_initial(1000, 0.8), 800)

    def test_doses_required(self):
        self.assertEqual(doses_required(800, 0.1), 880)

    def test_cost_before_adj(self):
        self.assertEqual(cost_before_adj(880, 0.2), 176)

    def test_political_multiplier(self):
        self.assertEqual(political_multiplier(0.3), 1.0)
        self.assertEqual(political_multiplier(0.5), 1.5)
        self.assertEqual(political_multiplier(0.8), 2.0)

    def test_delivery_channel_multiplier(self):
        self.assertEqual(delivery_channel_multiplier("Public"), 1.2)
        self.assertEqual(delivery_channel_multiplier("Mixed"), 1.0)
        self.assertEqual(delivery_channel_multiplier("Private"), 0.85)
        self.assertEqual(delivery_channel_multiplier("Other"), 1.0)

    def test_newborns(self):
        self.assertEqual(newborns("Goats", 800), 480)
        self.assertEqual(newborns("Sheep", 800), 320)
        self.assertEqual(newborns("Cattle", 800), 400)

    def test_second_year_coverage(self):
        self.assertEqual(second_year_coverage(480, 1.0), 480)
        self.assertEqual(second_year_coverage(480, 0.5), 240)

    def test_total_cost(self):
        self.assertEqual(total_cost(176, 1.5, 1.2), 316.8)

if __name__ == "__main__":
    unittest.main()
