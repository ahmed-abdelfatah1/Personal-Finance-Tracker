"""Category routes - CRUD operations for transaction categories."""

from decimal import Decimal
from typing import Optional

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user

from ..repositories import CategoryRepository

category_bp = Blueprint('category', __name__)


@category_bp.route('/categories')
@login_required
def categories():
    income_categories = CategoryRepository.get_income_categories(current_user.id)
    expense_categories = CategoryRepository.get_expense_categories(current_user.id)

    return render_template(
        'categories.html',
        income_categories=income_categories,
        expense_categories=expense_categories
    )


@category_bp.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    """Create a new category."""
    if request.method == 'GET':
        return render_template('add_category.html')

    try:
        name = request.form.get('name')
        category_type = request.form.get('category_type')
        color = request.form.get('color', '#3498db')
        max_single_amount = _parse_max_single_amount()

        if not name or not category_type:
            flash('Name and type are required', 'error')
            return redirect(url_for('category.add_category'))

        if category_type not in ['Income', 'Expense']:
            flash('Invalid category type', 'error')
            return redirect(url_for('category.add_category'))

        if CategoryRepository.exists_by_name_and_type(current_user.id, name, category_type):
            flash(f'Category "{name}" ({category_type}) already exists', 'error')
            return redirect(url_for('category.add_category'))

        CategoryRepository.create(
            user_id=current_user.id,
            name=name,
            category_type=category_type,
            color=color,
            max_single_amount=max_single_amount
        )

        flash(f'Category "{name}" created successfully!', 'success')
        return redirect(url_for('category.categories'))

    except Exception as e:
        flash(f'Error creating category: {str(e)}', 'error')
        return redirect(url_for('category.add_category'))


@category_bp.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id: int):
    """Edit an existing category."""
    category = CategoryRepository.get_by_id_and_user(category_id, current_user.id)

    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('category.categories'))

    if request.method == 'GET':
        return render_template('edit_category.html', category=category)

    return _update_category(category)


def _update_category(category):
    """Process category update form submission."""
    try:
        name = request.form.get('name')
        color = request.form.get('color', category.color)
        max_single_amount = _parse_max_single_amount()

        if not name:
            flash('Category name is required', 'error')
            return redirect(url_for('category.edit_category', category_id=category.id))

        if CategoryRepository.exists_by_name_and_type(
            current_user.id, name, category.category_type, exclude_id=category.id
        ):
            flash(f'Category "{name}" ({category.category_type}) already exists', 'error')
            return redirect(url_for('category.edit_category', category_id=category.id))

        CategoryRepository.update(
            category,
            name=name,
            color=color,
            max_single_amount=max_single_amount
        )
        flash(f'Category "{name}" updated successfully!', 'success')
        return redirect(url_for('category.categories'))

    except Exception as e:
        flash(f'Error updating category: {str(e)}', 'error')
        return redirect(url_for('category.edit_category', category_id=category.id))


def _parse_max_single_amount() -> Optional[Decimal]:
    """Parse max_single_amount from form, returning None if empty or invalid."""
    max_amount_str = request.form.get('max_single_amount', '').strip()
    if not max_amount_str:
        return None
    try:
        amount = Decimal(max_amount_str)
        return amount if amount > 0 else None
    except (ValueError, TypeError):
        return None




@category_bp.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id: int):
    category = CategoryRepository.get_by_id_and_user(category_id, current_user.id)

    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('category.categories'))

    can_delete, reason = CategoryRepository.can_delete(category.id)
    if not can_delete:
        category_name = category.name
        flash(
            f'Cannot delete category "{category_name}" because it {reason}.',
            'error'
        )
        return redirect(url_for('category.categories'))

    try:
        category_name = category.name
        CategoryRepository.delete(category)
        flash(f'Category "{category_name}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting category: {str(e)}', 'error')

    return redirect(url_for('category.categories'))

