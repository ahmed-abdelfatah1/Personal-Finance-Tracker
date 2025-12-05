"""Category routes - CRUD operations for transaction categories."""

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Category, Transaction, Budget

category_bp = Blueprint('category', __name__)


@category_bp.route('/categories')
@login_required
def categories():
    user_categories = Category.query.filter_by(user_id=current_user.id).all()

    income_categories = [c for c in user_categories if c.category_type == 'Income']
    expense_categories = [c for c in user_categories if c.category_type == 'Expense']

    return render_template(
        'categories.html',
        income_categories=income_categories,
        expense_categories=expense_categories
    )


@category_bp.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'GET':
        return render_template('add_category.html')

    try:
        name = request.form.get('name')
        category_type = request.form.get('category_type')
        color = request.form.get('color', '#3498db')

        if not name or not category_type:
            flash('Name and type are required', 'error')
            return redirect(url_for('category.add_category'))

        if category_type not in ['Income', 'Expense']:
            flash('Invalid category type', 'error')
            return redirect(url_for('category.add_category'))

        existing = Category.query.filter_by(
            user_id=current_user.id,
            name=name,
            category_type=category_type
        ).first()

        if existing:
            flash(f'Category "{name}" ({category_type}) already exists', 'error')
            return redirect(url_for('category.add_category'))

        new_category = Category(
            user_id=current_user.id,
            name=name,
            category_type=category_type,
            color=color
        )

        db.session.add(new_category)
        db.session.commit()

        flash(f'Category "{name}" created successfully!', 'success')
        return redirect(url_for('category.categories'))

    except Exception as e:
        flash(f'Error creating category: {str(e)}', 'error')
        return redirect(url_for('category.add_category'))


@category_bp.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id: int):
    category = Category.query.filter_by(
        id=category_id,
        user_id=current_user.id
    ).first()

    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('category.categories'))

    transaction_count = Transaction.query.filter_by(category_id=category.id).count()
    if transaction_count > 0:
        flash(
            f'Cannot delete category "{category.name}" because it has '
            f'{transaction_count} transactions. Delete or reassign transactions first.',
            'error'
        )
        return redirect(url_for('category.categories'))

    budget_count = Budget.query.filter_by(category_id=category.id).count()
    if budget_count > 0:
        flash(
            f'Cannot delete category "{category.name}" because it has '
            f'{budget_count} budgets. Delete budgets first.',
            'error'
        )
        return redirect(url_for('category.categories'))

    try:
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{category.name}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting category: {str(e)}', 'error')

    return redirect(url_for('category.categories'))

