"""Tests for pylotoncycle.pylotoncycle module."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pylotoncycle.pylotoncycle import PylotonCycle, PelotonLoginException


class TestPylotonCycleInit(unittest.TestCase):
    """Tests for PylotonCycle initialization."""

    @patch("pylotoncycle.pylotoncycle.AutoRefreshingSession")
    def test_init_with_valid_credentials(self, mock_session_class):
        """Test initialization with valid username and password."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "username": "testuser",
            "id": "user123",
            "total_workouts": 42,
        }
        mock_session.get.return_value = mock_response

        conn = PylotonCycle(username="test@example.com", password="secret")

        self.assertEqual(conn.username, "testuser")
        self.assertEqual(conn.userid, "user123")
        self.assertEqual(conn.total_workouts, 42)

    @patch("pylotoncycle.pylotoncycle.AutoRefreshingSession")
    def test_init_with_tokens(self, mock_session_class):
        """Test initialization with access and refresh tokens."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "username": "tokenuser",
            "id": "user456",
            "total_workouts": 100,
        }
        mock_session.get.return_value = mock_response

        conn = PylotonCycle(
            access_token="valid_access_token_here",
            refresh_token="valid_refresh_token_here",
        )

        self.assertEqual(conn.userid, "user456")

    @patch("pylotoncycle.pylotoncycle.AutoRefreshingSession")
    def test_init_short_tokens_ignored(self, mock_session_class):
        """Test that short tokens are treated as None."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "username": "user",
            "id": "id",
            "total_workouts": 0,
        }
        mock_session.get.return_value = mock_response

        PylotonCycle(access_token="short", refresh_token="tiny")

        call_kwargs = mock_session_class.call_args[1]
        self.assertIsNone(call_kwargs["access_token"])
        self.assertIsNone(call_kwargs["refresh_token"])


class TestGetMe(unittest.TestCase):
    """Tests for GetMe method."""

    @patch("pylotoncycle.pylotoncycle.AutoRefreshingSession")
    def test_get_me_success(self, mock_session_class):
        """Test GetMe returns user data on success."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "username": "testuser",
            "id": "user123",
            "total_workouts": 50,
            "email": "test@example.com",
        }
        mock_session.get.return_value = mock_response

        conn = PylotonCycle(username="test", password="pass")
        result = conn.GetMe()

        self.assertEqual(result["username"], "testuser")
        self.assertEqual(result["email"], "test@example.com")

    @patch("pylotoncycle.pylotoncycle.AutoRefreshingSession")
    def test_get_me_http_error(self, mock_session_class):
        """Test GetMe raises exception on HTTP error."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 401
        mock_session.get.return_value = mock_response

        with self.assertRaises(PelotonLoginException) as ctx:
            PylotonCycle(username="test", password="pass")

        self.assertIn("HTTP 401", str(ctx.exception))

    @patch("pylotoncycle.pylotoncycle.AutoRefreshingSession")
    def test_get_me_invalid_json(self, mock_session_class):
        """Test GetMe raises exception on invalid JSON response."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_session.get.return_value = mock_response

        with self.assertRaises(PelotonLoginException) as ctx:
            PylotonCycle(username="test", password="pass")

        self.assertIn("Invalid API response", str(ctx.exception))

    @patch("pylotoncycle.pylotoncycle.AutoRefreshingSession")
    def test_get_me_missing_field(self, mock_session_class):
        """Test GetMe raises exception when required field is missing."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"username": "test"}
        mock_session.get.return_value = mock_response

        with self.assertRaises(PelotonLoginException) as ctx:
            PylotonCycle(username="test", password="pass")

        self.assertIn("Missing expected field", str(ctx.exception))


class TestWorkoutMethods(unittest.TestCase):
    """Tests for workout-related methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch(
            "pylotoncycle.pylotoncycle.AutoRefreshingSession"
        )
        self.mock_session_class = self.patcher.start()
        self.mock_session = MagicMock()
        self.mock_session_class.return_value = self.mock_session

        mock_me_response = Mock()
        mock_me_response.status_code = 200
        mock_me_response.json.return_value = {
            "username": "testuser",
            "id": "user123",
            "total_workouts": 5,
        }
        self.mock_session.get.return_value = mock_me_response

        self.conn = PylotonCycle(username="test", password="pass")

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_get_workout_by_id(self):
        """Test GetWorkoutById returns workout data."""
        workout_data = {
            "id": "workout123",
            "fitness_discipline": "cycling",
            "ride": {"title": "30 min Power Zone"},
        }

        mock_response = Mock()
        mock_response.json.return_value = workout_data
        self.mock_session.get.return_value = mock_response

        result = self.conn.GetWorkoutById("workout123")

        self.assertEqual(result["id"], "workout123")
        self.assertEqual(result["ride"]["title"], "30 min Power Zone")

    def test_get_workout_metrics_by_id(self):
        """Test GetWorkoutMetricsById returns metrics data."""
        metrics_data = {
            "duration": 1800,
            "metrics": [{"slug": "output", "values": [100, 150, 200]}],
        }

        mock_response = Mock()
        mock_response.json.return_value = metrics_data
        self.mock_session.get.return_value = mock_response

        result = self.conn.GetWorkoutMetricsById("workout123")

        self.assertEqual(result["duration"], 1800)

    def test_get_workout_metrics_frequency(self):
        """Test GetWorkoutMetricsById respects frequency parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        self.mock_session.get.return_value = mock_response

        self.conn.GetWorkoutMetricsById("workout123", frequency=10)

        call_url = self.mock_session.get.call_args[0][0]
        self.assertIn("every_n=10", call_url)

    def test_get_instructor_by_id_caching(self):
        """Test that instructor data is cached."""
        instructor_data = {"id": "inst1", "name": "Alex Toussaint"}

        mock_response = Mock()
        mock_response.json.return_value = instructor_data
        self.mock_session.get.return_value = mock_response

        result1 = self.conn.GetInstructorById("inst1")
        result2 = self.conn.GetInstructorById("inst1")

        self.assertEqual(result1["name"], "Alex Toussaint")
        self.assertEqual(result2["name"], "Alex Toussaint")

        get_calls = [
            c
            for c in self.mock_session.get.call_args_list
            if "instructor" in str(c)
        ]
        self.assertEqual(len(get_calls), 1)


class TestGetWorkoutList(unittest.TestCase):
    """Tests for GetWorkoutList method."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch(
            "pylotoncycle.pylotoncycle.AutoRefreshingSession"
        )
        self.mock_session_class = self.patcher.start()
        self.mock_session = MagicMock()
        self.mock_session_class.return_value = self.mock_session

        mock_me_response = Mock()
        mock_me_response.status_code = 200
        mock_me_response.json.return_value = {
            "username": "testuser",
            "id": "user123",
            "total_workouts": 150,
        }
        self.mock_session.get.return_value = mock_me_response

        self.conn = PylotonCycle(username="test", password="pass")

    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()

    def test_get_workout_list_pagination(self):
        """Test GetWorkoutList handles pagination correctly."""
        page1_data = {"data": [{"id": f"w{i}"} for i in range(100)]}
        page2_data = {"data": [{"id": f"w{i}"} for i in range(100, 150)]}

        responses = [
            Mock(json=Mock(return_value=page1_data)),
            Mock(json=Mock(return_value=page2_data)),
        ]

        self.mock_session.get.side_effect = responses

        result = self.conn.GetWorkoutList(num_workouts=150)

        self.assertEqual(len(result), 150)

    def test_get_workout_list_small_request(self):
        """Test GetWorkoutList with fewer than 100 workouts."""
        page_data = {"data": [{"id": f"w{i}"} for i in range(25)]}

        mock_response = Mock()
        mock_response.json.return_value = page_data
        self.mock_session.get.return_value = mock_response

        result = self.conn.GetWorkoutList(num_workouts=25)

        self.assertEqual(len(result), 25)


if __name__ == "__main__":
    unittest.main()
