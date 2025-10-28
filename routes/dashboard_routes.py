
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import and_, func

from app import db
from models.carbon import Carbon
from models.goal import Goal
from models.user import User


dashboard_bp = Blueprint('dashboard', __name__)


def get_date_range(range_type):
    today = datetime.now().date()
    
    if range_type == 'day':
        return today, today
    elif range_type == 'week':
        # Monday to Sunday
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start, end
    elif range_type == 'month':
        # First day to last day of month
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(day=31)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
            end = next_month - timedelta(days=1)
        return start, end
    
    return today, today


def calculate_category_breakdown(entries):

    total_transport = sum(entry.transport for entry in entries)
    total_energy = sum(entry.energy for entry in entries)
    total = total_transport + total_energy
    
    if total == 0:
        return {
            'totals': {'transport': 0, 'food': 0, 'energy': 0, 'total': 0},
            'percentages': {'transport': 0, 'food': 0, 'energy': 0}
        }
    
    return {
        'totals': {
            'transport': round(total_transport, 2),
            'energy': round(total_energy, 2),
            'total': round(total, 2)
        },
        'percentages': {
            'transport': round((total_transport / total * 100), 1),
            'energy': round((total_energy / total * 100), 1)
        }
    }


@dashboard_bp.route('', methods=['GET'])
@jwt_required()
def get_dashboard():
    try:
        user_id = get_jwt_identity()
        range_type = request.args.get('range', 'week')
        
        # Validate range type
        if range_type not in ['day', 'week', 'month']:
            return jsonify({
                'success': False,
                'error': 'Invalid range type. Must be day, week, or month'
            }), 400
        
        # Get date range
        start_date, end_date = get_date_range(range_type)
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # ===== GET CURRENT PERIOD ENTRIES =====
        entries = Carbon.query.filter(
            and_(
                Carbon.user_id == user_id,
                Carbon.date >= start_date,
                Carbon.date <= end_date
            )
        ).order_by(Carbon.date).all()
        
        # Calculate current period totals
        breakdown = calculate_category_breakdown(entries)
        total_co2 = breakdown['totals']['total']
        
        # ===== GET PREVIOUS PERIOD FOR COMPARISON =====
        period_length = (end_date - start_date).days + 1
        prev_start = start_date - timedelta(days=period_length)
        prev_end = start_date - timedelta(days=1)
        
        prev_entries = Carbon.query.filter(
            and_(
                Carbon.user_id == user_id,
                Carbon.date >= prev_start,
                Carbon.date <= prev_end
            )
        ).all()
        
        prev_total = sum(entry.total for entry in prev_entries)
        change_percent = ((prev_total - total_co2) / prev_total * 100) if prev_total > 0 else 0
        
        # ===== FORMAT CHART DATA =====
        chart_data = []
        for entry in entries:
            date_format = '%a' if range_type == 'week' else '%m/%d'
            chart_data.append({
                'date': entry.date.strftime(date_format),
                'transport': round(entry.transport, 1),
                'energy': round(entry.energy, 1),
                'total': round(entry.total, 1)
            })
        
        category_data = [
            {
                'name': 'Transport',
                'value': breakdown['percentages']['transport'],
                'total': breakdown['totals']['transport'],
                'color': '#3b82f6'
            },
            {
                'name': 'Energy',
                'value': breakdown['percentages']['energy'],
                'total': breakdown['totals']['energy'],
                'color': '#8b5cf6'
            }
        ]
        
        # ===== GOAL PROGRESS =====
        goal_progress = {}
        
        # Weekly goal
        if range_type in ['week', 'day']:
            weekly_goal = Goal.query.filter_by(
                user_id=user_id,
                goal_type='weekly',
                is_active=True
            ).first()
            
            if weekly_goal:
                progress = weekly_goal.calculate_progress(total_co2)
                goal_progress['weekly'] = {
                    'target': weekly_goal.target_value,
                    'current': progress['current'],
                    'percentage': progress['percentage'],
                    'remaining': progress['remaining'],
                    'is_met': progress['is_met'],
                    'status': progress['status']
                }
        
        # Monthly goal
        if range_type in ['month', 'week']:
            monthly_goal = Goal.query.filter_by(
                user_id=user_id,
                goal_type='monthly',
                is_active=True
            ).first()
            
            if monthly_goal:
                # Get month to date total
                month_start, month_end = get_date_range('month')
                month_entries = Carbon.query.filter(
                    and_(
                        Carbon.user_id == user_id,
                        Carbon.date >= month_start,
                        Carbon.date <= datetime.now().date()
                    )
                ).all()
                
                month_total = sum(entry.total for entry in month_entries)
                progress = monthly_goal.calculate_progress(month_total)
                
                goal_progress['monthly'] = {
                    'target': monthly_goal.target_value,
                    'current': progress['current'],
                    'percentage': progress['percentage'],
                    'remaining': progress['remaining'],
                    'is_met': progress['is_met'],
                    'status': progress['status']
                }
        
        # National/Global average (configurable)
        national_average = 9.8  # kg CO2 per day
        
        # Calculate user's daily average for this period
        user_average = total_co2 / len(entries) if entries else 0
        
        # Calculate difference
        difference = national_average - user_average
        difference_percent = (difference / national_average * 100) if national_average > 0 else 0
        
        comparison = {
            'user_average': round(user_average, 1),
            'national_average': national_average,
            'difference': round(difference, 1),
            'difference_percent': round(difference_percent, 1),
            'status': 'below' if user_average < national_average else 'above' if user_average > national_average else 'equal'
        }
        
        return jsonify({
            'success': True,
            'data': {
                'metrics': {
                    'total_co2': breakdown['totals']['total'],
                    'transport': breakdown['totals']['transport'],
                    'food': breakdown['totals']['food'],
                    'energy': breakdown['totals']['energy'],
                    'transport_percent': breakdown['percentages']['transport'],
                    'food_percent': breakdown['percentages']['food'],
                    'energy_percent': breakdown['percentages']['energy'],
                    'change_percent': round(change_percent, 1),
                    'trend': 'down' if change_percent > 0 else 'up' if change_percent < 0 else 'stable'
                },
                'chart_data': chart_data,
                'category_data': category_data,
                'goal_progress': goal_progress,
                'comparison': comparison,
                'metadata': {
                    'range': range_type,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'entry_count': len(entries),
                    'user_id': user_id
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
    try:
        user_id = get_jwt_identity()
        today = datetime.now().date()
        
        # Today's emissions
        today_entry = Carbon.query.filter_by(
            user_id=user_id,
            date=today
        ).first()
        
        # This week's total
        week_start = today - timedelta(days=today.weekday())
        week_entries = Carbon.query.filter(
            and_(
                Carbon.user_id == user_id,
                Carbon.date >= week_start,
                Carbon.date <= today
            )
        ).all()
        week_total = sum(entry.total for entry in week_entries)
        
        # This month's total
        month_start = today.replace(day=1)
        month_entries = Carbon.query.filter(
            and_(
                Carbon.user_id == user_id,
                Carbon.date >= month_start,
                Carbon.date <= today
            )
        ).all()
        month_total = sum(entry.total for entry in month_entries)
        
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
        
        return jsonify({
            'success': True,
            'data': {
                'today': {
                    'total': round(today_entry.total, 1) if today_entry else 0,
                    'has_entry': today_entry is not None
                },
                'week': {
                    'total': round(week_total, 1),
                    'goal': weekly_goal.target_value if weekly_goal else None,
                    'progress': round((week_total / weekly_goal.target_value * 100), 1) if weekly_goal else None
                },
                'month': {
                    'total': round(month_total, 1),
                    'goal': monthly_goal.target_value if monthly_goal else None,
                    'progress': round((month_total / monthly_goal.target_value * 100), 1) if monthly_goal else None
                },
                'entries_count': len(month_entries)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@dashboard_bp.route('/insights', methods=['GET'])
@jwt_required()
def get_insights():
 
    try:
        user_id = get_jwt_identity()
        
        # Get last 30 days of data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        entries = Carbon.query.filter(
            and_(
                Carbon.user_id == user_id,
                Carbon.date >= start_date,
                Carbon.date <= end_date
            )
        ).all()
        
        if not entries:
            return jsonify({
                'success': True,
                'data': {
                    'insights': [],
                    'message': 'Start tracking your emissions to get personalized insights!'
                }
            }), 200
        
        # Calculate category breakdown
        breakdown = calculate_category_breakdown(entries)
        
        insights = []
        
        # Highest category insight
        categories = breakdown['percentages']
        highest_category = max(categories, key=categories.get)
        highest_percent = categories[highest_category]
        
        if highest_percent > 40:
            insights.append({
                'type': 'high_category',
                'category': highest_category,
                'percentage': highest_percent,
                'message': f'{highest_category.capitalize()} accounts for {highest_percent}% of your emissions',
                'suggestion': f'Consider reducing your {highest_category} emissions for the biggest impact'
            })
        
        # Average daily emissions
        avg_daily = breakdown['totals']['total'] / len(entries)
        if avg_daily > 10:
            insights.append({
                'type': 'high_average',
                'value': round(avg_daily, 1),
                'message': f'Your average daily emissions ({avg_daily:.1f} kg) are above the recommended 8 kg',
                'suggestion': 'Try to reduce emissions by 20% through sustainable choices'
            })
        
        # Trend analysis
        first_week = entries[:7] if len(entries) >= 7 else entries
        last_week = entries[-7:] if len(entries) >= 7 else entries
        
        first_avg = sum(e.total for e in first_week) / len(first_week)
        last_avg = sum(e.total for e in last_week) / len(last_week)
        
        if last_avg < first_avg:
            improvement = ((first_avg - last_avg) / first_avg) * 100
            insights.append({
                'type': 'positive_trend',
                'improvement': round(improvement, 1),
                'message': f'Great job! Your emissions decreased by {improvement:.1f}% recently',
                'suggestion': 'Keep up the good work!'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'insights': insights,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': len(entries)
                },
                'summary': {
                    'total': breakdown['totals']['total'],
                    'average': round(avg_daily, 1),
                    'highest_category': highest_category
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    try:
        user_id = get_jwt_identity()
        period = request.args.get('period', 'week')
        limit = request.args.get('limit', 10, type=int)
        
        # Get date range
        start_date, end_date = get_date_range(period)
        
        # Aggregate emissions by user
        results = db.session.query(
            Carbon.user_id,
            func.sum(Carbon.transport + Carbon.energy).label('total_emissions'),
            func.count(Carbon.id).label('entry_count')
        ).filter(
            and_(
                Carbon.date >= start_date,
                Carbon.date <= end_date
            )
        ).group_by(Carbon.user_id).order_by('total_emissions').limit(limit).all()
        
        # Get user details and build leaderboard
        leaderboard = []
        user_rank = None
        
        for idx, (uid, total, count) in enumerate(results, 1):
            user = User.query.get(uid)
            entry = {
                'rank': idx,
                'user_id': uid,
                'username': user.username if user else 'Unknown',
                'display_name': user.display_name if user else 'Unknown',
                'total_emissions': round(total, 2),
                'entry_count': count,
                'average_daily': round(total / count, 2) if count > 0 else 0
            }
            leaderboard.append(entry)
            
            if uid == user_id:
                user_rank = entry
        
        return jsonify({
            'success': True,
            'data': {
                'leaderboard': leaderboard,
                'user_rank': user_rank,
                'period': period,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500