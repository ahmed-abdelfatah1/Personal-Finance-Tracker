"""Goal routes - financial goal setting and tracking."""

from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..repositories import GoalRepository

goal_bp = Blueprint('goal', __name__)


@goal_bp.route('/goals')
@login_required
def goals():
    """Display all goals for the current user."""
    user_goals = GoalRepository.get_all_by_user(current_user.id)
    return render_template('goals.html', goals=user_goals)


@goal_bp.route('/goals/add', methods=['GET', 'POST'])
@login_required
def add_goal():
    """Add a new financial goal."""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            target_amount = Decimal(request.form.get('target_amount', 0))
            current_amount = Decimal(request.form.get('current_amount', 0))
            target_date_str = request.form.get('target_date')
            description = request.form.get('description')

            # Validate inputs
            if not name or target_amount <= 0:
                flash('Please provide a valid goal name and target amount', 'error')
                return redirect(url_for('goal.add_goal'))

            # Parse target date if provided
            target_date = None
            if target_date_str:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()

            # Create new goal
            GoalRepository.create(
                user_id=current_user.id,
                name=name,
                target_amount=target_amount,
                current_amount=current_amount,
                target_date=target_date,
                description=description
            )

            flash(f'Goal "{name}" created successfully!', 'success')
            return redirect(url_for('goal.goals'))

        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return redirect(url_for('goal.add_goal'))
        except Exception as e:
            GoalRepository.rollback()
            flash(f'Error creating goal: {str(e)}', 'error')
            return redirect(url_for('goal.add_goal'))

    return render_template('goal_form.html', goal=None)


@goal_bp.route('/goals/<int:goal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_goal(goal_id):
    """Edit an existing goal."""
    goal = GoalRepository.get_by_id_and_user_or_404(goal_id, current_user.id)

    if request.method == 'POST':
        try:
            target_date_str = request.form.get('target_date')
            target_date = None
            if target_date_str:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()

            GoalRepository.update(
                goal,
                name=request.form.get('name'),
                target_amount=Decimal(request.form.get('target_amount', 0)),
                current_amount=Decimal(request.form.get('current_amount', 0)),
                target_date=target_date,
                description=request.form.get('description')
            )
            flash(f'Goal "{goal.name}" updated successfully!', 'success')
            return redirect(url_for('goal.goals'))

        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return redirect(url_for('goal.edit_goal', goal_id=goal_id))
        except Exception as e:
            GoalRepository.rollback()
            flash(f'Error updating goal: {str(e)}', 'error')
            return redirect(url_for('goal.edit_goal', goal_id=goal_id))

    return render_template('goal_form.html', goal=goal)


@goal_bp.route('/goals/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id):
    """Delete a goal."""
    goal = GoalRepository.get_by_id_and_user_or_404(goal_id, current_user.id)
    
    try:
        goal_name = goal.name
        GoalRepository.delete(goal)
        flash(f'Goal "{goal_name}" deleted successfully!', 'success')
    except Exception as e:
        GoalRepository.rollback()
        flash(f'Error deleting goal: {str(e)}', 'error')
    
    return redirect(url_for('goal.goals'))


@goal_bp.route('/goals/<int:goal_id>/update_progress', methods=['POST'])
@login_required
def update_progress(goal_id):
    """Update the current amount for a goal."""
    goal = GoalRepository.get_by_id_and_user_or_404(goal_id, current_user.id)
    
    try:
        amount_to_add = Decimal(request.form.get('amount', 0))
        
        if amount_to_add > 0:
            GoalRepository.add_progress(goal, amount_to_add)
            flash(f'Added {amount_to_add} EGP to goal "{goal.name}"!', 'success')
        else:
            flash('Please enter a valid amount', 'error')
    
    except ValueError:
        flash('Invalid amount entered', 'error')
    except Exception as e:
        GoalRepository.rollback()
        flash(f'Error updating progress: {str(e)}', 'error')
    
    return redirect(url_for('goal.goals'))
