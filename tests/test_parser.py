"""Tests for pylotoncycle.parser module."""

import unittest
from pylotoncycle.parser import ParseCyclingMetrics, ParseOutdoorRunMetrics


class TestParseCyclingMetrics(unittest.TestCase):

    def test_basic_parsing(self):
        json_resp = {
            "duration": 60,
            "segment_list": [
                {"name": "Warmup", "start_time_offset": 0, "length": 30},
                {"name": "Main", "start_time_offset": 30, "length": 30},
            ],
            "seconds_since_pedaling_start": [0, 30, 60],
            "metrics": [
                {"slug": "cadence", "values": [80, 90, 85]},
                {"slug": "output", "values": [100, 150, 120]},
            ],
        }

        result = ParseCyclingMetrics(json_resp)

        self.assertIn(0, result)
        self.assertIn(30, result)
        self.assertIn(60, result)

        self.assertEqual(result[0]["cadence"], 80)
        self.assertEqual(result[0]["output"], 100)
        self.assertEqual(result[0]["segment"], "Warmup")

        self.assertEqual(result[30]["cadence"], 90)
        self.assertEqual(result[30]["segment"], "Main")

    def test_segment_mapping(self):
        json_resp = {
            "duration": 100,
            "segment_list": [
                {"name": "Intro", "start_time_offset": 0, "length": 20},
                {"name": "Work", "start_time_offset": 20, "length": 60},
                {"name": "Cooldown", "start_time_offset": 80, "length": 20},
            ],
            "seconds_since_pedaling_start": [10, 50, 90],
            "metrics": [{"slug": "power", "values": [100, 200, 80]}],
        }

        result = ParseCyclingMetrics(json_resp)

        self.assertEqual(result[10]["segment"], "Intro")
        self.assertEqual(result[50]["segment"], "Work")
        self.assertEqual(result[90]["segment"], "Cooldown")

    def test_empty_segment_list(self):
        json_resp = {
            "duration": 30,
            "segment_list": [],
            "seconds_since_pedaling_start": [0, 15, 30],
            "metrics": [{"slug": "cadence", "values": [70, 75, 80]}],
        }

        result = ParseCyclingMetrics(json_resp)

        self.assertEqual(result[0]["segment"], None)
        self.assertEqual(result[15]["segment"], None)
        self.assertEqual(result[30]["segment"], None)

    def test_multiple_metrics(self):
        json_resp = {
            "duration": 10,
            "segment_list": [],
            "seconds_since_pedaling_start": [0, 5, 10],
            "metrics": [
                {"slug": "cadence", "values": [80, 85, 90]},
                {"slug": "resistance", "values": [40, 45, 50]},
                {"slug": "output", "values": [100, 120, 140]},
                {"slug": "speed", "values": [20.0, 22.5, 25.0]},
            ],
        }

        result = ParseCyclingMetrics(json_resp)

        self.assertEqual(result[5]["cadence"], 85)
        self.assertEqual(result[5]["resistance"], 45)
        self.assertEqual(result[5]["output"], 120)
        self.assertEqual(result[5]["speed"], 22.5)


class TestParseOutdoorRunMetrics(unittest.TestCase):

    def test_basic_parsing(self):
        json_resp = {
            "segment_list": [
                {"id": "seg1", "name": "Warmup", "metrics_type": "walking"},
                {"id": "seg2", "name": "Run", "metrics_type": "running"},
            ],
            "location_data": [
                {
                    "segment_id": "seg1",
                    "coordinates": [
                        {
                            "seconds_offset_from_start": 0,
                            "latitude": 40.7128,
                            "longitude": -74.0060,
                        },
                        {
                            "seconds_offset_from_start": 30,
                            "latitude": 40.7130,
                            "longitude": -74.0062,
                        },
                    ],
                },
                {
                    "segment_id": "seg2",
                    "coordinates": [
                        {
                            "seconds_offset_from_start": 60,
                            "latitude": 40.7135,
                            "longitude": -74.0065,
                        },
                    ],
                },
            ],
        }

        result = ParseOutdoorRunMetrics(json_resp)

        self.assertIn(0, result)
        self.assertIn(30, result)
        self.assertIn(60, result)

        self.assertEqual(result[0]["segment_name"], "Warmup")
        self.assertEqual(result[0]["segment_metrics_type"], "walking")
        self.assertEqual(result[0]["latitude"], 40.7128)

        self.assertEqual(result[60]["segment_name"], "Run")
        self.assertEqual(result[60]["segment_metrics_type"], "running")

    def test_preserves_coordinate_data(self):
        json_resp = {
            "segment_list": [
                {"id": "s1", "name": "Test", "metrics_type": "running"},
            ],
            "location_data": [
                {
                    "segment_id": "s1",
                    "coordinates": [
                        {
                            "seconds_offset_from_start": 100,
                            "latitude": 37.7749,
                            "longitude": -122.4194,
                            "altitude": 10.5,
                            "speed": 3.5,
                        },
                    ],
                },
            ],
        }

        result = ParseOutdoorRunMetrics(json_resp)

        self.assertEqual(result[100]["latitude"], 37.7749)
        self.assertEqual(result[100]["longitude"], -122.4194)
        self.assertEqual(result[100]["altitude"], 10.5)
        self.assertEqual(result[100]["speed"], 3.5)
        self.assertEqual(result[100]["segment_name"], "Test")


if __name__ == "__main__":
    unittest.main()
