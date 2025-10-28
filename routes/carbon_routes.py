
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import and_, func


from app import db
from models.carbon import Carbon
from models.user import User

carbon_bp = Blueprint('carbon', __name__)


@carbon_bp.route('/carbon', methods=['GET'])
@jwt_required()
def get_entries():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Carbon.query.filter_by(user_id=user_id)
        
        # Apply date filters
        if start_date:
            query = query.filter(Carbon.date >= datetime.fromisoformat(start_date).date())
        if end_date:
            query = query.filter(Carbon.date <= datetime.fromisoformat(end_date).date())
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        entries = query.order_by(Carbon.date.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': [entry.to_dict() for entry in entries],
            'metadata': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'count': len(entries)
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid date format: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@carbon_bp.route('/carbon', methods=['POST'])
@jwt_required()
def create_entry():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['transport', 'food', 'energy']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing)}'
            }), 400
        
        # Parse date or use today
        entry_date = datetime.now().date()
        if 'date' in data:
            entry_date = datetime.fromisoformat(data['date']).date()
        
        # Check for existing entry on this date
        existing = Carbon.query.filter_by(
            user_id=user_id,
            date=entry_date
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': f'Entry already exists for {entry_date}. Use PUT to update.',
                'existing_entry_id': existing.id
            }), 409
        
        # Create new entry
        entry = Carbon(
            user_id=user_id,
            date=entry_date,
            transport=float(data['transport']),
            food=float(data['food']),
            energy=float(data['energy']),
            notes=data.get('notes')
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Carbon entry created successfully',
            'data': entry.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid data format: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@carbon_bp.route('/carbon/<int:entry_id>', methods=['GET'])
@jwt_required()
def get_entry(entry_id):
    """
    Get specific carbon entry by ID
    
    Args:
        entry_id (int): Carbon entry ID
        
    Returns:
        JSON: Entry data
    """
    try:
        user_id = get_jwt_identity()
        entry = Carbon.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({
                'success': False,
                'error': 'Entry not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': entry.to_dict(include_percentages=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@carbon_bp.route('/carbon/<int:entry_id>', methods=['PUT'])
@jwt_required()
def update_entry(entry_id):
    try:
        user_id = get_jwt_identity()
        entry = Carbon.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({
                'success': False,
                'error': 'Entry not found'
            }), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'transport' in data:
            entry.transport = float(data['transport'])
        if 'food' in data:
            entry.food = float(data['food'])
        if 'energy' in data:
            entry.energy = float(data['energy'])
        if 'notes' in data:
            entry.notes = data['notes']
        
        entry.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Entry updated successfully',
            'data': entry.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid data format: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@carbon_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@jwt_required()
def delete_entry(entry_id):
    try:
        user_id = get_jwt_identity()
        entry = Carbon.query.filter_by(id=entry_id, user_id=user_id).first()
        
        if not entry:
            return jsonify({
                'success': False,
                'error': 'Entry not found'
            }), 404
        
        db.session.delete(entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Entry deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



# ANALYTICS & AGGREGATIONS

@carbon_bp.route('/categories/totals', methods=['GET'])
@jwt_required()
def get_category_totals():
    try:
        user_id = get_jwt_identity()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = Carbon.query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(Carbon.date >= datetime.fromisoformat(start_date).date())
        if end_date:
            query = query.filter(Carbon.date <= datetime.fromisoformat(end_date).date())
        
        entries = query.all()
        
        # Calculate totals
        total_transport = sum(entry.transport for entry in entries)
        total_food = sum(entry.food for entry in entries)
        total_energy = sum(entry.energy for entry in entries)
        total = total_transport + total_food + total_energy
        
        # Calculate percentages
        percentages = {
            'transport': round((total_transport / total * 100), 1) if total > 0 else 0,
            'food': round((total_food / total * 100), 1) if total > 0 else 0,
            'energy': round((total_energy / total * 100), 1) if total > 0 else 0
        }
        
        return jsonify({
            'success': True,
            'data': {
                'totals': {
                    'transport': round(total_transport, 2),
                    'food': round(total_food, 2),
                    'energy': round(total_energy, 2),
                    'total': round(total, 2)
                },
                'percentages': percentages,
                'entry_count': len(entries)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@carbon_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    try:
        user_id = get_jwt_identity()
        today = datetime.now().date()
        
        # Today's entry
        today_entry = Carbon.query.filter_by(
            user_id=user_id,
            date=today
        ).first()
        
        # This week (Monday to Sunday)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_entries = Carbon.query.filter(
            Carbon.user_id == user_id,
            Carbon.date >= week_start,
            Carbon.date <= week_end
        ).all()
        
        # This month
        month_start = today.replace(day=1)
        month_entries = Carbon.query.filter(
            Carbon.user_id == user_id,
            Carbon.date >= month_start,
            Carbon.date <= today
        ).all()
        
        # This year
        year_start = today.replace(month=1, day=1)
        year_entries = Carbon.query.filter(
            Carbon.user_id == user_id,
            Carbon.date >= year_start,
            Carbon.date <= today
        ).all()
        
        return jsonify({
            'success': True,
            'data': {
                'today': {
                    'total': round(today_entry.total, 2) if today_entry else 0,
                    'has_entry': today_entry is not None
                },
                'week': {
                    'total': round(sum(e.total for e in week_entries), 2),
                    'average': round(sum(e.total for e in week_entries) / len(week_entries), 2) if week_entries else 0,
                    'entries': len(week_entries)
                },
                'month': {
                    'total': round(sum(e.total for e in month_entries), 2),
                    'average': round(sum(e.total for e in month_entries) / len(month_entries), 2) if month_entries else 0,
                    'entries': len(month_entries)
                },
                'year': {
                    'total': round(sum(e.total for e in year_entries), 2),
                    'average': round(sum(e.total for e in year_entries) / len(year_entries), 2) if year_entries else 0,
                    'entries': len(year_entries)
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@carbon_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    try:
        user_id = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        
        # Current period
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        current_entries = Carbon.query.filter(
            Carbon.user_id == user_id,
            Carbon.date >= start_date,
            Carbon.date <= end_date
        ).order_by(Carbon.date).all()
        
        # Previous period
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days)
        
        prev_entries = Carbon.query.filter(
            Carbon.user_id == user_id,
            Carbon.date >= prev_start,
            Carbon.date <= prev_end
        ).all()
        
        # Calculate totals
        current_total = sum(e.total for e in current_entries)
        prev_total = sum(e.total for e in prev_entries)
        
        # Calculate change
        change_amount = current_total - prev_total
        change_percent = ((change_amount / prev_total) * 100) if prev_total > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'current_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'total': round(current_total, 2),
                    'average': round(current_total / len(current_entries), 2) if current_entries else 0,
                    'entries': [e.to_chart_data('%Y-%m-%d') for e in current_entries]
                },
                'previous_period': {
                    'start_date': prev_start.isoformat(),
                    'end_date': prev_end.isoformat(),
                    'total': round(prev_total, 2),
                    'average': round(prev_total / len(prev_entries), 2) if prev_entries else 0
                },
                'comparison': {
                    'change_amount': round(change_amount, 2),
                    'change_percent': round(change_percent, 1),
                    'trend': 'up' if change_amount > 0 else 'down' if change_amount < 0 else 'stable'
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@carbon_bp.route('/streak', methods=['GET'])
@jwt_required()
def get_streak():
    try:
        user_id = get_jwt_identity()
        
        # Get all entries ordered by date
        entries = Carbon.query.filter_by(user_id=user_id).order_by(Carbon.date.desc()).all()
        
        if not entries:
            return jsonify({
                'success': True,
                'data': {
                    'current_streak': 0,
                    'longest_streak': 0,
                    'last_entry_date': None
                }
            }), 200
        
        # Calculate current streak
        current_streak = 0
        expected_date = datetime.now().date()
        
        for entry in entries:
            if entry.date == expected_date:
                current_streak += 1
                expected_date -= timedelta(days=1)
            else:
                break
        
        # Calculate longest streak
        longest_streak = 0
        temp_streak = 1
        
        for i in range(len(entries) - 1):
            if (entries[i].date - entries[i + 1].date).days == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
        
        return jsonify({
            'success': True,
            'data': {
                'current_streak': current_streak,
                'longest_streak': longest_streak,
                'last_entry_date': entries[0].date.isoformat(),
                'total_entries': len(entries)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500