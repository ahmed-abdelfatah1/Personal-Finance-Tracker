"""Transaction Template routes - CRUD operations for transaction templates."""

from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user

from ..repositories import (
    TransactionTemplateRepository,
    AccountRepository,
    CategoryRepository
)

template_bp = Blueprint('template', __name__)


@template_bp.route('/templates')
@login_required
def templates():
    """Display all transaction templates for the current user."""
    all_templates = TransactionTemplateRepository.get_all_by_user(current_user.id)
    income_templates = TransactionTemplateRepository.get_by_type(current_user.id, 'Income')
    expense_templates = TransactionTemplateRepository.get_by_type(current_user.id, 'Expense')

    return render_template(
        'templates.html',
        templates=all_templates,
        income_templates=income_templates,
        expense_templates=expense_templates
    )


@template_bp.route('/templates/add', methods=['GET', 'POST'])
@login_required
def add_template():
    """Add a new transaction template."""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            transaction_type = request.form.get('transaction_type')
            default_amount_str = request.form.get('default_amount', '')
            account_id_str = request.form.get('account_id', '')
            category_id_str = request.form.get('category_id', '')
            description = request.form.get('description', '')

            if not name or not transaction_type:
                flash('Name and transaction type are required', 'error')
                return redirect(url_for('template.add_template'))

            if transaction_type not in ['Income', 'Expense']:
                flash('Invalid transaction type', 'error')
                return redirect(url_for('template.add_template'))

            default_amount = None
            if default_amount_str:
                default_amount = Decimal(default_amount_str)

            account_id = None
            if account_id_str:
                account_id = int(account_id_str)
                # Verify account belongs to user
                account = AccountRepository.get_by_id_and_user(account_id, current_user.id)
                if not account:
                    flash('Invalid account selected', 'error')
                    return redirect(url_for('template.add_template'))

            category_id = None
            if category_id_str:
                category_id = int(category_id_str)
                # Verify category belongs to user
                category = CategoryRepository.get_by_id_and_user(category_id, current_user.id)
                if not category:
                    flash('Invalid category selected', 'error')
                    return redirect(url_for('template.add_template'))

            TransactionTemplateRepository.create(
                user_id=current_user.id,
                name=name,
                transaction_type=transaction_type,
                default_amount=default_amount,
                account_id=account_id,
                category_id=category_id,
                description=description if description else None
            )

            flash(f'Template "{name}" created successfully!', 'success')
            return redirect(url_for('template.templates'))

        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return redirect(url_for('template.add_template'))
        except Exception as e:
            from ..extensions import db
            db.session.rollback()
            flash(f'Error creating template: {str(e)}', 'error')
            return redirect(url_for('template.add_template'))

    accounts = AccountRepository.get_all_by_user(current_user.id)
    categories = CategoryRepository.get_all_by_user(current_user.id)

    return render_template(
        'template_form.html',
        template=None,
        accounts=accounts,
        categories=categories
    )


@template_bp.route('/templates/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(template_id: int):
    """Edit an existing transaction template."""
    template = TransactionTemplateRepository.get_by_id_and_user_or_404(
        template_id, current_user.id
    )

    if request.method == 'POST':
        try:
            default_amount_str = request.form.get('default_amount', '')
            account_id_str = request.form.get('account_id', '')
            category_id_str = request.form.get('category_id', '')

            default_amount = None
            if default_amount_str:
                default_amount = Decimal(default_amount_str)

            account_id = None
            if account_id_str:
                account_id = int(account_id_str)
                account = AccountRepository.get_by_id_and_user(account_id, current_user.id)
                if not account:
                    flash('Invalid account selected', 'error')
                    return redirect(url_for('template.edit_template', template_id=template_id))

            category_id = None
            if category_id_str:
                category_id = int(category_id_str)
                category = CategoryRepository.get_by_id_and_user(category_id, current_user.id)
                if not category:
                    flash('Invalid category selected', 'error')
                    return redirect(url_for('template.edit_template', template_id=template_id))

            TransactionTemplateRepository.update(
                template,
                name=request.form.get('name'),
                transaction_type=request.form.get('transaction_type'),
                default_amount=default_amount,
                account_id=account_id,
                category_id=category_id,
                description=request.form.get('description') or None
            )

            flash(f'Template "{template.name}" updated successfully!', 'success')
            return redirect(url_for('template.templates'))

        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return redirect(url_for('template.edit_template', template_id=template_id))
        except Exception as e:
            from ..extensions import db
            db.session.rollback()
            flash(f'Error updating template: {str(e)}', 'error')
            return redirect(url_for('template.edit_template', template_id=template_id))

    accounts = AccountRepository.get_all_by_user(current_user.id)
    categories = CategoryRepository.get_all_by_user(current_user.id)

    return render_template(
        'template_form.html',
        template=template,
        accounts=accounts,
        categories=categories
    )


@template_bp.route('/templates/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id: int):
    """Delete a transaction template."""
    template = TransactionTemplateRepository.get_by_id_and_user_or_404(
        template_id, current_user.id
    )

    try:
        template_name = template.name
        TransactionTemplateRepository.delete(template)
        flash(f'Template "{template_name}" deleted successfully!', 'success')
    except Exception as e:
        from ..extensions import db
        db.session.rollback()
        flash(f'Error deleting template: {str(e)}', 'error')

    return redirect(url_for('template.templates'))


@template_bp.route('/templates/<int:template_id>/use', methods=['POST'])
@login_required
def use_template(template_id: int):
    """Use a template to create a transaction (redirects to add transaction with pre-filled data)."""
    template = TransactionTemplateRepository.get_by_id_and_user_or_404(
        template_id, current_user.id
    )

    # Redirect to add transaction page with template data in session or URL params
    # For simplicity, we'll use URL parameters
    params = {
        'template_name': template.name,
        'type': template.transaction_type,
    }
    if template.default_amount:
        params['amount'] = str(template.default_amount)
    if template.account_id:
        params['account_id'] = str(template.account_id)
    if template.category_id:
        params['category_id'] = str(template.category_id)
    if template.description:
        params['description'] = template.description

    return redirect(url_for('transaction.add_transaction', **params))

