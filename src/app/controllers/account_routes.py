"""Account routes - CRUD operations for financial accounts."""

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Account, Transaction

account_bp = Blueprint('account', __name__)


@account_bp.route('/accounts')
@login_required
def accounts(): 
    user_accounts = Account.query.filter_by(user_id=current_user.id).all()
    total_balance = sum(acc.current_balance for acc in user_accounts)

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
        initial_balance = float(request.form.get('initial_balance', 0))

        if not name:
            flash('Account name is required', 'error')
            return redirect(url_for('account.add_account'))

        new_account = Account(
            user_id=current_user.id,
            name=name,
            account_type=account_type,
            initial_balance=initial_balance,
            current_balance=initial_balance
        )

        db.session.add(new_account)
        db.session.commit()

        flash(f'Account "{name}" created successfully!', 'success')
        return redirect(url_for('account.accounts'))

    except ValueError:
        flash('Invalid balance amount', 'error')
        return redirect(url_for('account.add_account'))
    except Exception as e:
        flash(f'Error creating account: {str(e)}', 'error')
        return redirect(url_for('account.add_account'))


@account_bp.route('/edit_account/<int:account_id>', methods=['GET', 'POST'])
@login_required
def edit_account(account_id: int):
    account = Account.query.filter_by(
        id=account_id,
        user_id=current_user.id
    ).first()

    if not account:
        flash('Account not found', 'error')
        return redirect(url_for('account.accounts'))

    if request.method == 'GET':
        return render_template('edit_account.html', account=account)

    try:
        account.name = request.form.get('name')
        account.account_type = request.form.get('account_type')

        transaction_count = Transaction.query.filter_by(account_id=account.id).count()
        if transaction_count == 0:
            new_initial = float(request.form.get('initial_balance', 0))
            difference = new_initial - float(account.initial_balance)
            account.initial_balance = new_initial
            account.current_balance = float(account.current_balance) + difference

        db.session.commit()
        flash('Account updated successfully!', 'success')
        return redirect(url_for('account.accounts'))

    except ValueError:
        flash('Invalid balance amount', 'error')
        return redirect(url_for('account.edit_account', account_id=account_id))
    except Exception as e:
        flash(f'Error updating account: {str(e)}', 'error')
        return redirect(url_for('account.edit_account', account_id=account_id))


@account_bp.route('/delete_account/<int:account_id>', methods=['POST'])
@login_required
def delete_account(account_id: int):
    account = Account.query.filter_by(
        id=account_id,
        user_id=current_user.id
    ).first()

    if not account:
        flash('Account not found', 'error')
        return redirect(url_for('account.accounts'))

    transaction_count = Transaction.query.filter_by(account_id=account.id).count()
    if transaction_count > 0:
        flash(
            f'Cannot delete account "{account.name}" because it has '
            f'{transaction_count} transactions. Delete transactions first.',
            'error'
        )
        return redirect(url_for('account.accounts'))

    try:
        db.session.delete(account)
        db.session.commit()
        flash(f'Account "{account.name}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting account: {str(e)}', 'error')

    return redirect(url_for('account.accounts'))

