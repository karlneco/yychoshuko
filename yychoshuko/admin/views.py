from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, logout_user
from werkzeug.security import generate_password_hash

from yychoshuko import db
from yychoshuko.models import Grade, User, staff_grade
from yychoshuko.util import admin_required

admin_bp = Blueprint('admin', __name__, template_folder='templates')


@admin_bp.route('/admin')
@admin_bp.route('/main', methods=['GET'])
@login_required
def admin_main():
    return render_template('home.html')


@admin_bp.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect('/')


@admin_bp.route('/staff')
@login_required
@admin_required
def staff_list():
    staff = User.query.all()
    user_types = {
        'T': 'Teacher',
        'H': 'Teacher Assistant',
        'A': 'Administrator',
        'N': 'Not Specified'
    }

    return render_template('staff_list.html', staff=staff, user_types=user_types)


@admin_bp.route('/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def staff_edit(staff_id):
    # Load the teacher data from the database based on user_id
    staff = User.query.get(staff_id)

    # If the staff member does not exist, return a 404 error
    if not staff:
        abort(404)

    staff_grades = [{'id': c.id, 'name': c.name} for c in staff.grades]

    grades = Grade.query.all()
    all_grades = [{'id': c.id, 'name': c.name} for c in grades]

    if request.method == 'POST':
        # Update teacher data based on form input
        staff.name = request.form['name']
        staff.email = request.form['email']
        staff.is_active = 'is_active' in request.form
        staff.user_type = request.form['user_type']

        # Commit changes to the database
        db.session.commit()

        # Redirect to the teacher list or another page
        return redirect(url_for('admin.staff_list'))

    return render_template('staff_edit.html', staff=staff, grades=staff_grades, all_grades=all_grades)


@admin_bp.route('/courses')
@login_required
@admin_required
def course_list():
    courses = Grade.query.all()
    return render_template('grades.html', courses=courses)


@admin_bp.route('/admin/reset_password/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(staff_id):
    if request.method == 'POST':
        new_password = request.form['new_password']

        # Retrieve the teacher from the database
        staff = User.query.get(staff_id)

        if staff is not None:
            # Set the new password for the teacher
            staff.password_hash = generate_password_hash(
                new_password)  # Ensure you have the correct password hashing function

            # Commit changes to the database
            db.session.commit()

            flash('Password reset successful', 'success')
        else:
            flash('Staff member not found', 'error')

        return redirect(url_for('admin.staff_edit', staff_id=staff_id))


# Route to get the classes for a specific teacher
@admin_bp.route('/api/staff_grades/<int:staff_id>', methods=['GET'])
@login_required
@admin_required
def get_staff_classes(staff_id):
    staff = User.query.get(staff_id)
    if staff:
        grades = [{'id': c.id, 'name': c.name} for c in staff.grades]
        return jsonify({'grades': grades})
    else:
        return jsonify({'classes': []})


# Route to get all available classes
@admin_bp.route('/api/all_grades', methods=['GET'])
@login_required
@admin_required
def get_all_classes():
    grades = Grade.query.all()
    all_grades = [{'id': c.id, 'name': c.name} for c in grades]
    return jsonify({'grades': all_grades})

@admin_bp.route('/api/add_grade/<int:grade_id>/<int:staff_id>', methods=['GET'])
@login_required
@admin_required
def add_class(grade_id, staff_id):
    staff = User.query.get(staff_id)
    grade_to_add = Grade.query.get(grade_id)

    if staff and grade_to_add:
        staff.grades.append(grade_to_add)
        db.session.commit()
        return jsonify({'message': 'Class added successfully'})
    else:
        return jsonify({'error': 'Teacher or class not found'})

# Route to remove a class from a teacher
@admin_bp.route('/api/remove_grade/<int:grade_id>/<int:staff_id>', methods=['GET'])
@login_required
@admin_required
def remove_class(grade_id, staff_id):
    staff = User.query.get(staff_id)
    grade_to_remove = Grade.query.get(grade_id)

    if staff and grade_to_remove:
        # Find all instances of the association and delete them
        association_table = staff_grade
        association_query = association_table.delete().where(
            association_table.c.user_id == staff_id,
            association_table.c.grade_id == grade_id
        )
        db.session.execute(association_query)
        db.session.commit()

        return jsonify({'message': 'Class removed successfully'})
    else:
        return jsonify({'error': 'Teacher or class not found'})


@admin_bp.route('/delete_staff/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def delete_staff(staff_id):
    # Retrieve the staff member from the database
    staff = User.query.get(staff_id)

    if staff:
        # Remove associations with any classes
        staff.classes = []

        # Delete the staff member from the database
        db.session.delete(staff)
        db.session.commit()

        flash('Staff member deleted successfully', 'success')
        return redirect(url_for('admin.staff_list'))
    else:
        flash('Staff member not found', 'error')
        return redirect(url_for('admin.staff_list'))