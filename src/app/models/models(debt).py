from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()
class Debt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    principal = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=0.0)
    remaining_balance = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, default=datetime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class DebtPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime)
    debt_id = db.Column(db.Integer, db.ForeignKey('debt.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)