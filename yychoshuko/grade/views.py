from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from yychoshuko import db
from yychoshuko.models import Grade, load_grade
from yychoshuko.util import admin_required

grade_bp = Blueprint('grade', __name__, template_folder='templates')


@grade_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        instructions = request.form['instructions']
        day_start_str = request.form['day_start']
        lunch_start_str = request.form['lunch_start']
        lunch_end_str = request.form['lunch_end']
        day_end_str = request.form['day_end']
        day_start = datetime.strptime(day_start_str, '%H:%M').time() if day_start_str else None
        lunch_start = datetime.strptime(lunch_start_str, '%H:%M').time() if lunch_start_str else None
        lunch_end = datetime.strptime(lunch_end_str, '%H:%M').time() if lunch_end_str else None
        day_end = datetime.strptime(day_end_str, '%H:%M').time() if day_end_str else None

        try:
            class_obj = Grade(
                name=name, instructions=instructions,
                day_start=day_start, lunch_start=lunch_start,
                lunch_end=lunch_end, day_end=day_end
            )
            db.session.add(class_obj)
            db.session.commit()
            return redirect(url_for('admin.course_list'))
        except IntegrityError:
            db.session.rollback()  # Roll back the transaction so you can continue using the session
            flash('A class with that name already exists. Please use a different name.', 'danger')
            return render_template('grade_create.html', name=name, instructions=instructions,
                                   day_start=day_start, lunch_start=lunch_start,
                                   lunch_end=lunch_end, day_end=day_end)
    return render_template('grade_create.html')


@grade_bp.route('/edit/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(course_id):
    grade = Grade.query.get_or_404(course_id)
    # Filter staff into teachers and assistants
    teachers = [user for user in grade.staff if user.user_type == 'T']
    assistants = [user for user in grade.staff if user.user_type == 'H']

    if request.method == 'POST':
        # Since no editing of teachers or assistants, only handle other fields
        grade.name = request.form['name']
        grade.instructions = request.form['instructions']
        day_start_str = request.form['day_start']
        lunch_start_str = request.form['lunch_start']
        lunch_end_str = request.form['lunch_end']
        day_end_str = request.form['day_end']
        grade.day_start = datetime.strptime(day_start_str, '%H:%M').time() if day_start_str else None
        grade.lunch_start = datetime.strptime(lunch_start_str, '%H:%M').time() if lunch_start_str else None
        grade.lunch_end = datetime.strptime(lunch_end_str, '%H:%M').time() if lunch_end_str else None
        grade.day_end = datetime.strptime(day_end_str, '%H:%M').time() if day_end_str else None
        db.session.commit()

        if request.form['action'] == 'duplicate':
            # Duplicate logic
            new_course = Grade(name="Copy of " + grade.name, instructions=grade.instructions, day_start=grade.day_start,
                               lunch_start=grade.lunch_start, day_end=grade.day_end, lunch_end=grade.lunch_end)
            db.session.add(new_course)
            db.session.commit()
            return redirect(url_for('grade.edit', course_id=new_course.id))

        return redirect(url_for('admin.course_list'))

    return render_template('grade_edit.html', course=grade, teachers=teachers, assistants=assistants)


@grade_bp.route('/duplicate/<int:grade_id>', methods=['POST'])
@login_required
@admin_required
def duplicate(grade_id):
    original_grade = Grade.query.get_or_404(grade_id)
    new_grade = Grade(
        name="Copy of " + original_grade.name,
        instructions=original_grade.instructions,
        day_start=original_grade.day_start,
        lunch_start=original_grade.lunch_start,
        lunch_end=original_grade.lunch_end,
        day_end=original_grade.day_end,
        # Ensure any other fields are copied as necessary
    )
    db.session.add(new_grade)
    db.session.commit()
    flash('Grade duplicated successfully. Please edit the name.')
    return redirect(url_for('grade.edit', grade_id=new_grade.id))


@grade_bp.route('/delete/<int:grade_id>', methods=['GET'])
@login_required
@admin_required
def delete(grade_id):
    grade = Grade.query.get_or_404(grade_id)
    db.session.delete(grade)
    db.session.commit()
    flash('Grade deleted successfully.')
    return redirect(url_for('grade.course_list'))


@grade_bp.route('/grade_view', methods=['GET', 'POST'])
@login_required
@admin_required
def grade_view():
    grade = load_grade()
    return render_template('grade_edit.html', grade=grade)


@grade_bp.route('/grade_list')
@login_required
@admin_required
def grade_list():
    grades = Grade.query.all()
    return render_template(url_for('admin.grade_list'))
