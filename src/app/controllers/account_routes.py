"""Account routes - CRUD operations for financial accounts."""

from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user

from ..repositories import AccountRepository, TransactionRepository

account_bp = Blueprint('account', __name__)


@account_bp.route('/accounts')
@login_required
def accounts():
    user_accounts = AccountRepository.get_all_by_user(current_user.id)
    total_balance = AccountRepository.get_total_balance(current_user.id)

    return render_template(
        'accounts.html',
        accounts=user_accounts,
        total_balance=total_balance
    )


@account_bp.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    if request.method == 'GET':
        return render_template('add_account.html')

    try:
        name = request.form.get('name')
        account_type = request.form.get('account_type')
        initial_balance = Decimal(str(request.form.get('initial_balance', 0)))

        if not name:
            flash('Account name is required', 'error')
            return redirect(url_for('account.add_account'))

        AccountRepository.create(
            user_id=current_user.id,
            name=name,
            account_type=account_type,
            initial_balance=initial_balance
        )

        flash(f'Account "{name}" created successfully!', 'success')
        return redirect(url_for('account.accounts'))

    except (ValueError, TypeError):
        flash('Invalid balance amount', 'error')
        return redirect(url_for('account.add_account'))
    except Exception as e:
        flash(f'Error creating account: {str(e)}', 'error')
        return redirect(url_for('account.add_account'))


@account_bp.route('/edit_account/<int:account_id>', methods=['GET', 'POST'])
@login_required
def edit_account(account_id: int):
    account = AccountRepository.get_by_id_and_user(account_id, current_user.id)

    if not account:
        flash('Account not found', 'error')
        return redirect(url_for('account.accounts'))

    if request.method == 'GET':
        return render_template('edit_account.html', account=account)

    try:
        update_data = {
            'name': request.form.get('name'),
            'account_type': request.form.get('account_type')
        }

        if not AccountRepository.has_transactions(account.id):
            new_initial = Decimal(str(request.form.get('initial_balance', 0)))
            difference = new_initial - account.initial_balance
            update_data['initial_balance'] = new_initial
            update_data['current_balance'] = account.current_balance + difference

        AccountRepository.update(account, **update_data)
        flash('Account updated successfully!', 'success')
        return redirect(url_for('account.accounts'))

    except (ValueError, TypeError):
        flash('Invalid balance amount', 'error')
        return redirect(url_for('account.edit_account', account_id=account_id))
    except Exception as e:
        flash(f'Error updating account: {str(e)}', 'error')
        return redirect(url_for('account.edit_account', account_id=account_id))


@account_bp.route('/delete_account/<int:account_id>', methods=['POST'])
@login_required
def delete_account(account_id: int):
    account = AccountRepository.get_by_id_and_user(account_id, current_user.id)

    if not account:
        flash('Account not found', 'error')
        return redirect(url_for('account.accounts'))

    if AccountRepository.has_transactions(account.id):
        transaction_count = AccountRepository.get_transaction_count(account.id)
        flash(
            f'Cannot delete account "{account.name}" because it has '
            f'{transaction_count} transactions. Delete transactions first.',
            'error'
        )
        return redirect(url_for('account.accounts'))

    try:
        account_name = account.name
        AccountRepository.delete(account)
        flash(f'Account "{account_name}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting account: {str(e)}', 'error')

    return redirect(url_for('account.accounts'))

