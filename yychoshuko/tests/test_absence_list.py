import unittest
from datetime import date, datetime, timedelta
from flask import url_for
from base_test import BaseTestCase, db
from yychoshuko.models import User, Grade, Absence


class TestListAbsences(BaseTestCase):

    def setUp(self):
        super().setUp()
        # Create an admin user who can see all grades.
        self.admin = User(
            email="admin@example.com",
            password="password",  # Plain-text; in practice you'll hash this.
            name="Admin User",
            user_type="A"
        )
        db.session.add(self.admin)
        db.session.commit()

        # Log in as admin.
        # Using the same login endpoint as in your teacher tests.
        self.client.post(url_for('staff.staff_login'),
                         data=dict(username="admin@example.com", password="password"),
                         follow_redirects=True)

        # Create a Grade record so that absence form choices are populated.
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

        # Create an Absence record for that grade.
        self.absence_date = date(2025, 2, 20)
        self.absence = Absence(
            student_name="山田太郎",
            reason="欠席",
            class_id=self.grade.id,  # Note: your route uses 'class_id' to store the grade id.
            date=self.absence_date,
            start_time=datetime.strptime("09:00", "%H:%M").time(),
            end_time=datetime.strptime("15:00", "%H:%M").time(),
            parent_email="parent@example.com",
            absence_type="欠席",
            comment="病気のため"
        )
        db.session.add(self.absence)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_list_absences_with_date_filter(self):
        """Test that listing absences with a date filter shows the correct absence."""
        # Call the list route with filterDate query parameter.
        response = self.client.get(url_for('absences.list', filterDate=self.absence_date.strftime("%Y-%m-%d")))
        # Check that the student's name appears in the response.
        self.assertIn("山田太郎".encode('utf-8'), response.data)
        # Check that the absence date appears in the response.
        self.assertIn(self.absence_date.strftime("%Y-%m-%d").encode('utf-8'), response.data)

    def test_list_absences_without_date_filter(self):
        """Test that listing absences without a date filter shows the absence."""
        response = self.client.get(url_for('absences.list'))
        self.assertIn("山田太郎".encode('utf-8'), response.data)


if __name__ == '__main__':
    unittest.main()
