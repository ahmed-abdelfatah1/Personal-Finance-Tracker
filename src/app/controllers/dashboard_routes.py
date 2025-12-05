"""Dashboard routes - main dashboard view."""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..models import Transaction

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    total_balance = current_user.get_total_balance()

    recent_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.desc()).limit(5).all()

    monthly_summary = {'income': 0, 'expenses': 0, 'net': 0}

    return render_template(
        'dashboard.html',
        user=current_user,
        total_balance=total_balance,
        recent_transactions=recent_transactions,
        monthly_summary=monthly_summary
    )

