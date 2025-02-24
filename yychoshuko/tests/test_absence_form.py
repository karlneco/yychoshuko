import unittest
from datetime import datetime
from flask import url_for
from base_test import BaseTestCase, db
from yychoshuko.models import Grade, Absence

class TestAbsenceForm(BaseTestCase):

    def setUp(self):
        super().setUp()
        # Create a Grade record so the absence form has a valid choice.
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

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_valid_absence_submission(self):
        """
        Test a valid absence submission.
        Using reason 'その他' should cause the form to append the 'other_reason' data.
        """
        # Data for a valid absence submission.
        data = {
            "student_name": "山田太郎",
            "date": "2025-02-20",
            "reason": "その他",
            "other_reason": "交通機関の遅延",
            "class_id": str(self.grade.id),
            "parent_email": "parent@example.com",
            "absence_type": "欠席",
            "start_time": "09:00",
            "end_time": "15:00",
            "comment": "具合が悪い"
        }
        response = self.client.post(url_for('absences.record_absence'), data=data, follow_redirects=True)
        self.assertIn("連絡フォームのご提出をありがとうございました。".encode('utf-8'), response.data)

        # Verify that an absence record was created.
        absence = Absence.query.filter_by(student_name="山田太郎").first()
        self.assertIsNotNone(absence)
        # For reason 'その他', the route concatenates the text.
        self.assertEqual(absence.reason, "その他: 交通機関の遅延")

    def test_absence_submission_missing_start_time_for_late(self):
        """
        Test absence submission for a late arrival.
        When reason is '遅刻' and start_time is missing, the form should fail validation
        and flash the error message for start_time.
        """
        data = {
            "student_name": "山田花子",
            "date": "2025-02-20",
            "reason": "体調不良",
            "class_id": str(self.grade.id),
            "parent_email": "parent@example.com",
            "absence_type": "遅刻",
            # "start_time" is intentionally omitted
            "end_time": "15:00",
            "comment": "遅刻テスト"
        }
        response = self.client.post(url_for('absences.record_absence'), data=data, follow_redirects=True)
        # The conditional validator for '遅刻' appends an error on start_time.
        self.assertIn(b"Expected time is required for", response.data)

if __name__ == '__main__':
    unittest.main()
