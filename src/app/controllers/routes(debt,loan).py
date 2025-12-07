from flask import Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Account, Category, Transaction, Debt, DebtPayment
from datetime import datetime
import csv
from io import StringIO

bp = Blueprint('routes', __name__)

@bp.route('/import_csv', methods=['POST'])
@login_required
def import_csv():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.csv'):
        flash('Invalid CSV file')
        return redirect(request.url)

    stream = StringIO(file.stream.read().decode('UTF-8'))
    reader = csv.reader(stream)
    next(reader)

    imported = 0
    skipped = 0

    for row in reader:
        if len(row) < 5:
            skipped += 1
            continue

        try:
            date_str = row[0].strip()
            trans_type = row[1].strip().capitalize()
            amount = float(row[2].strip())
            description = row[3].strip()
            account_name = row[4].strip()
            category_name = row[5].strip() if len(row) > 5 else None

            if trans_type not in ['Income', 'Expense']:
                skipped += 1
                continue

            date = datetime.strptime(date_str, '%Y-%m-%d')

            account = Account.query.filter_by(user_id=current_user.id, name=account_name).first()
            if not account:
                account = Account(name=account_name, balance=0.0, user_id=current_user.id)
                db.session.add(account)

            category = None
            if category_name:
                category = Category.query.filter_by(user_id=current_user.id, name=category_name).first()

            if trans_type == 'Income':
                account.balance += amount
            else:
                account.balance -= amount

            transaction = Transaction(
                amount=amount,
                type=trans_type,
                date=date,
                description=description,
                account_id=account.id,
                category_id=category.id if category else None,
                user_id=current_user.id
            )
            db.session.add(transaction)
            imported += 1

        except Exception:
            skipped += 1

    db.session.commit()
    flash(f'Imported {imported} transactions ({skipped} skipped)')
    return redirect(url_for('routes.transactions'))


@bp.route('/debts', methods=['GET'])
@login_required
def get_debts():
    debts = Debt.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': d.id,
        'name': d.name,
        'principal': d.principal,
        'remaining_balance': d.remaining_balance,
        'interest_rate': d.interest_rate
    } for d in debts])


@bp.route('/debts', methods=['POST'])
@login_required
def add_debt():
    data = request.get_json() or request.form
    debt = Debt(
        name=data['name'],
        principal=float(data['principal']),
        interest_rate=float(data.get('interest_rate', 0)),
        remaining_balance=float(data['principal']),
        user_id=current_user.id
    )
    db.session.add(debt)
    db.session.commit()
    flash('Debt added')
    return redirect(url_for('routes.debts'))


@bp.route('/debts/<int:debt_id>/pay', methods=['POST'])
@login_required
def pay_debt(debt_id):
    debt = Debt.query.get_or_404(debt_id)
    if debt.user_id != current_user.id:
        flash('Unauthorized')
        return redirect(url_for('routes.debts'))

    data = request.get_json() or request.form
    amount = float(data['amount'])

    if amount > debt.remaining_balance:
        flash('Payment exceeds balance')
    else:
        debt.remaining_balance -= amount
        payment = DebtPayment(amount=amount, debt_id=debt.id, user_id=current_user.id)
        db.session.add(payment)
        db.session.commit()
        flash('Payment recorded')
    return redirect(url_for('routes.debts'))


@bp.route('/reports/monthly_cashflow')
@login_required
def monthly_cashflow_report():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    monthly = {}

    for t in transactions:
        key = t.date.strftime('%Y-%m')
        if key not in monthly:
            monthly[key] = {'income': 0.0, 'expense': 0.0}
        if t.type == 'Income':
            monthly[key]['income'] += t.amount
        else:
            monthly[key]['expense'] += t.amount

    result = []
    for month in sorted(monthly.keys(), reverse=True):
        data = monthly[month]
        result.append({
            'month': month,
            'income': round(data['income'], 2),
            'expense': round(data['expense'], 2),
            'net_cashflow': round(data['income'] - data['expense'], 2)
        })

    return jsonify({'monthly_report': result})