from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.carbon import CarbonEntry
from models.user import User
from models.goal import Goal
from app import db
from datetime import datetime, timedelta
from sqlalchemy import and_, func

dashboard_bp = Blueprint('dashboard', __name__)

def get_date_range(range_type):
    """Get start and end dates based on range type"""
    today = datetime.now().date()
    
    if range_type == 'day':
        return today, today
    elif range_type == 'week':
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start, end
    elif range_type == 'month':
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(day=31)
        else:
            end = (today.replace(month=today.month + 1, day=1) - timedelta(days=1))
        return start, end
    return today, today

@dashboard_bp.route('', methods=['GET'])
@jwt_required()
def get_dashboard():
    """
    Get comprehensive dashboard data including metrics, charts, and comparisons
    
    Query Parameters:
        range (str): Date range - 'day', 'week', or 'month' (default: 'week')
    
    Returns:
        JSON with metrics, chart_data, category_data, goal_progress, and comparison
    """
    try:
        user_id = get_jwt_identity()
        range_type = request.args.get('range', 'week')
        
        if range_type not in ['day', 'week', 'month']:
            return jsonify({'error': 'Invalid range type. Must be day, week, or month'}), 400
        
        start_date, end_date = get_date_range(range_type)
        
        # Get entries for the period
        entries = CarbonEntry.query.filter(
            and_(
                CarbonEntry.user_id == user_id,
                CarbonEntry.date >= start_date,
                CarbonEntry.date <= end_date
            )
        ).order_by(CarbonEntry.date).all()
        
        # Calculate totals
        total_transport = sum(entry.transport for entry in entries)
        total_food = sum(entry.food for entry in entries)
        total_energy = sum(entry.energy for entry in entries)
        total_co2 = total_transport + total_food + total_energy
        
        # Calculate percentages
        transport_percent = (total_transport / total_co2 * 100) if total_co2 > 0 else 0
        food_percent = (total_food / total_co2 * 100) if total_co2 > 0 else 0
        energy_percent = (total_energy / total_co2 * 100) if total_co2 > 0 else 0
        
        # Get previous period for comparison
        period_length = (end_date - start_date).days + 1
        prev_start = start_date - timedelta(days=period_length)
        prev_end = start_date - timedelta(days=1)
        
        prev_entries = CarbonEntry.query.filter(
            and_(
                CarbonEntry.user_id == user_id,
                CarbonEntry.date >= prev_start,
                CarbonEntry.date <= prev_end
            )
        ).all()
        
        prev_total = sum(entry.total for entry in prev_entries)
        change_percent = ((prev_total - total_co2) / prev_total * 100) if prev_total > 0 else 0
        
        # Format chart data
        chart_data = []
        for entry in entries:
            chart_data.append({
                'date': entry.date.strftime('%a') if range_type == 'week' else entry.date.strftime('%m/%d'),
                'transport': round(entry.transport, 1),
                'food': round(entry.food, 1),
                'energy': round(entry.energy, 1),
                'total': round(entry.total, 1)
            })
        
        # Category breakdown
        category_data = [
            {'name': 'Transport', 'value': round(transport_percent), 'color': '#3b82f6'},
            {'name': 'Food', 'value': round(food_percent), 'color': '#f59e0b'},
            {'name': 'Energy', 'value': round(energy_percent), 'color': '#8b5cf6'}
        ]
        
        # Get active goals
        weekly_goal = Goal.query.filter_by(
            user_id=user_id, 
            goal_type='weekly', 
            is_active=True
        ).first()
        
        monthly_goal = Goal.query.filter_by(
            user_id=user_id, 
            goal_type='monthly', 
            is_active=True
        ).first()
        
        # Calculate goal progress
        goal_progress = {}
        if weekly_goal:
            weekly_progress = (total_co2 / weekly_goal.target_value * 100) if range_type == 'week' else 0
            goal_progress['weekly'] = {
                'target': weekly_goal.target_value,
                'current': round(total_co2, 1),
                'progress': min(round(weekly_progress, 1), 100),
                'remaining': max(round(weekly_goal.target_value - total_co2, 1), 0)
            }
        
        if monthly_goal and range_type in ['week', 'month']:
            month_start, month_end = get_date_range('month')
            month_entries = CarbonEntry.query.filter(
                and_(
                    CarbonEntry.user_id == user_id,
                    CarbonEntry.date >= month_start,
                    CarbonEntry.date <= month_end
                )
            ).all()
            month_total = sum(entry.total for entry in month_entries)
            monthly_progress = (month_total / monthly_goal.target_value * 100)
            goal_progress['monthly'] = {
                'target': monthly_goal.target_value,
                'current': round(month_total, 1),
                'progress': min(round(monthly_progress, 1), 100),
                'remaining': max(round(monthly_goal.target_value - month_total, 1), 0)
            }
        
        # National average (configurable)
        national_average = 9.8
        user_average = total_co2 / len(entries) if entries else 0
        comparison_percent = ((national_average - user_average) / national_average * 100) if national_average > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'metrics': {
                    'total_co2': round(total_co2, 1),
                    'transport': round(total_transport, 1),
                    'food': round(total_food, 1),
                    'energy': round(total_energy, 1),
                    'transport_percent': round(transport_percent, 1),
                    'food_percent': round(food_percent, 1),
                    'energy_percent': round(energy_percent, 1),
                    'change_percent': round(change_percent, 1)
                },
                'chart_data': chart_data,
                'category_data': category_data,
                'goal_progress': goal_progress,
                'comparison': {
                    'user_average': round(user_average, 1),
                    'national_average': national_average,
                    'difference_percent': round(comparison_percent, 1)
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    """Get quick summary statistics"""
    try:
        user_id = get_jwt_identity()
        today = datetime.now().date()
        
        # Today's emissions
        today_entry = CarbonEntry.query.filter_by(
            user_id=user_id,
            date=today
        ).first()
        
        # This week's total
        week_start = today - timedelta(days=today.weekday())
        week_entries = CarbonEntry.query.filter(
            and_(
                CarbonEntry.user_id == user_id,
                CarbonEntry.date >= week_start,
                CarbonEntry.date <= today
            )
        ).all()
        
        week_total = sum(entry.total for entry in week_entries)
        
        # This month's total
        month_start = today.replace(day=1)
        month_entries = CarbonEntry.query.filter(
            and_(
                CarbonEntry.user_id == user_id,
                CarbonEntry.date >= month_start,
                CarbonEntry.date <= today
            )
        ).all()
        
        month_total = sum(entry.total for entry in month_entries)
        
        return jsonify({
            'success': True,
            'data': {
                'today': round(today_entry.total, 1) if today_entry else 0,
                'week': round(week_total, 1),
                'month': round(month_total, 1),
                'entries_count': len(month_entries)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500