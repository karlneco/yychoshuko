import unittest
from datetime import date, datetime, timedelta
from flask import url_for
from bs4 import BeautifulSoup
from base_test import BaseTestCase, db
from yychoshuko.models import User, Grade, Semester, Absence

class TestAbsencesByStudentTemplate(BaseTestCase):

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

        # Create a Semester record covering today's date.
        today = date.today()
        self.semester = Semester(
            name="学期1",
            start_date=today - timedelta(days=5),
            end_date=today + timedelta(days=5)
        )
        db.session.add(self.semester)
        db.session.commit()

        # Create a Grade record (which in this context is used to populate the class choices).
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

        # Create an Absence record for a student in this grade.
        self.absence = Absence(
            student_name="山田太郎",
            reason="欠席",
            class_id=self.grade.id,  # In your route, absences are filtered by class_id.
            date=today,
            start_time=datetime.strptime("09:00", "%H:%M").time(),
            end_time=datetime.strptime("15:00", "%H:%M").time(),
            parent_email="parent@example.com",
            absence_type="欠席",  # For '欠席', your logic adds 1 to the absence days.
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

    def test_students_template_rendering(self):
        # Call the route with the semester_id query parameter.
        response = self.client.get(url_for('absences.students', semester_id=self.semester.id))
        self.assertEqual(response.status_code, 200)

        # Parse the HTML using BeautifulSoup.
        soup = BeautifulSoup(response.data, 'html.parser')

        # Verify that the header "生徒別欠課概要" appears.
        header = soup.find('h1')
        self.assertIsNotNone(header)
        self.assertEqual(header.get_text(strip=True), "生徒別欠課概要")

        # Verify the semester select dropdown exists and contains options.
        select = soup.find('select', id="semesterSelect")
        self.assertIsNotNone(select)
        options = select.find_all('option')
        self.assertGreater(len(options), 0)

        # Verify that the option for our semester is selected.
        selected_option = select.find('option', selected=True)
        self.assertIsNotNone(selected_option)
        expected_option_text = f"{self.semester.name} ({self.semester.start_date.strftime('%Y-%m-%d')} - {self.semester.end_date.strftime('%Y-%m-%d')})"
        self.assertEqual(selected_option.get_text(strip=True), expected_option_text)

        # Verify that there is a table with headers for student name, absence days, and absence hours.
        table = soup.find('table', class_="table")
        self.assertIsNotNone(table)
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        self.assertIn("生徒氏名", headers)
        self.assertIn("欠席日数", headers)
        self.assertIn("欠課時間", headers)

        # Verify that the student's name "山田太郎" appears as a link in the table.
        student_link = table.find('a', string="山田太郎")
        self.assertIsNotNone(student_link)

        # Verify that the absence days are correctly rendered (should be "1" for one absence).
        row = student_link.find_parent('tr')
        cells = row.find_all('td')
        # The second cell should contain the absence days.
        self.assertEqual(cells[1].get_text(strip=True), "1")

        # Verify the absence hours: since the absence type is "欠席", the hours are not increased,
        # so we expect the duration to be 0. Also, the cell has a data attribute with the raw value.
        duration_cell = cells[2]
        self.assertTrue(duration_cell.has_attr('data-hours'))
        self.assertEqual(duration_cell['data-hours'], "0")

if __name__ == '__main__':
    unittest.main()
