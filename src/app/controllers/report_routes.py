"""Report routes - financial reports and analytics."""

from flask import Blueprint, render_template
from flask_login import login_required

report_bp = Blueprint('report', __name__)


@report_bp.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

