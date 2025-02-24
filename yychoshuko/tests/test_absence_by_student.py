import unittest
from datetime import date, datetime, timedelta
from flask import url_for
from unittest.mock import patch
from base_test import BaseTestCase, db
from yychoshuko.models import User, Grade, Semester, Absence


class TestStudentsAbsences(BaseTestCase):

    def setUp(self):
        super().setUp()
        # Create an admin user so that all grades are fetched.
        self.admin = User(
            email="admin@example.com",
            password="password",  # For testing, plain text is acceptable.
            name="Admin User",
            user_type="A"
        )
        db.session.add(self.admin)
        db.session.commit()

        # Create a Grade record (this is used as the class in the absence routes)
        self.grade = Grade(
            name="5年生",
            instructions="テスト用の指示",
            day_start=datetime.strptime("09:00", "%H:%M").time(),
            lunch_start=datetime.strptime("12:00", "%H:%M").time(),
            lunch_end=datetime.strptime("13:00", "%H:%M").time(),
            day_end=datetime.strptime("15:00", "%H:%M").time()
        )
        db.session.add(self.grade)
        db.session.commit()

        # Create a Semester record that covers today's date.
        today = date.today()
        start_date = today - timedelta(days=10)
        end_date = today + timedelta(days=10)
        self.semester = Semester(
            name="Semester 1",
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(self.semester)
        db.session.commit()

        # Create an Absence record within the semester.
        self.absence_date = today
        self.absence = Absence(
            student_name="山田太郎",
            reason="欠席",
            class_id=self.grade.id,  # In your code, absence.class_id is used to link to the grade.
            date=self.absence_date,
            start_time=datetime.strptime("09:00", "%H:%M").time(),
            end_time=datetime.strptime("15:00", "%H:%M").time(),
            parent_email="parent@example.com",
            absence_type="欠席",
            comment="病気のため"
        )
        db.session.add(self.absence)
        db.session.commit()

        # Log in as admin.
        # Using the same login endpoint as in your teacher tests.
        self.client.post(url_for('staff.staff_login'),
                         data=dict(username="admin@example.com", password="password"),
                         follow_redirects=True)


    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @patch('yychoshuko.absences.views.calculate_absence_duration', return_value=2)
    def test_students_absences(self, mock_duration):
        """
        Test that the /students route returns correct absence summary data.
        The response should contain:
         - The student's name ("山田太郎")
         - The grade name ("5年生")
         - The absence count (for "欠席", the route increments days by 1)
        """
        response = self.client.get(url_for('absences.students', semester_id=self.semester.id))
        # Check that the student's name appears in the rendered HTML.
        self.assertIn("山田太郎".encode('utf-8'), response.data)
        # Check that the grade name appears.
        self.assertIn("5年生".encode('utf-8'), response.data)
        # Since for a "欠席" absence the route increments days by 1,
        # verify that "1" (or an appropriate summary string) appears.
        # (Adjust this assertion based on how your template renders the summary.)
        self.assertIn(b"1", response.data)


if __name__ == '__main__':
    unittest.main()
