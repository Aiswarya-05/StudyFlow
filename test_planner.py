
import unittest
from main import create_study_plan
from io import StringIO
from contextlib import redirect_stdout


class TestStudyPlanner(unittest.TestCase):

    def test_two_hours_three_subjects(self):
        output = StringIO()

        with redirect_stdout(output):
            result = create_study_plan(
                2, ["Java", "SQL", "Python"]
            )

        self.assertEqual(
            result, "Study plan created successfully."
        )
        self.assertIn("Java (40 minutes)", output.getvalue())
        self.assertIn("SQL (40 minutes)", output.getvalue())
        self.assertIn("Python (40 minutes)", output.getvalue())

    def test_invalid_hours(self):
        result = create_study_plan(0, ["Java"])
        self.assertEqual(
            result, "Please enter a positive number of hours."
        )

    def test_no_subjects(self):
        result = create_study_plan(2, [])
        self.assertEqual(
            result, "Please enter at least one subject."
        )


if __name__ == "__main__":
    unittest.main()
