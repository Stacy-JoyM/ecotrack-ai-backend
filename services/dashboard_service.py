from datetime import datetime, timedelta
from models.dashboard import CarbonEmission, UserGoal, NationalAverage
from app import db


class DashboardService:
    """Service class for dashboard business logic"""
    
    @staticmethod
    def get_date_range(date_range):
        """Get start and end dates based on filter"""
        now = datetime.now()
        end_date = now.date()
        
        if date_range == 'day':
            start_date = end_date
        elif date_range == 'week':
            start_date = (now - timedelta(days=7)).date()
        elif date_range == 'month':
            start_date = (now - timedelta(days=30)).date()
        else:
            start_date = (now - timedelta(days=7)).date()
        
        return start_date, end_date
    
    @staticmethod
    def get_carbon_data(user_id, date_range='week'):
        """Get carbon emissions data for charts"""
        start_date, end_date = DashboardService.get_date_range(date_range)
        
        emissions = CarbonEmission.get_by_date_range(user_id, start_date, end_date)
        
        # Format data for frontend
        return [
            {
                'date': DashboardService.format_date(emission.date, date_range),
                'transport': emission.transport,
                'food': emission.food,
                'energy': emission.energy,
                'total': emission.total
            }
            for emission in emissions
        ]
    
    @staticmethod
    def get_category_breakdown(user_id, date_range='week'):
        """Get category breakdown for pie chart"""
        start_date, end_date = DashboardService.get_date_range(date_range)
        
        totals = CarbonEmission.get_category_totals(user_id, start_date, end_date)
        
        total = totals['total'] if totals['total'] > 0 else 1  # Avoid division by zero
        
        return [
            {
                'name': 'Transport',
                'value': round((totals['transport'] / total) * 100),
                'color': '#3b82f6'
            },
            {
                'name': 'Food',
                'value': round((totals['food'] / total) * 100),
                'color': '#f59e0b'
            },
            {
                'name': 'Energy',
                'value': round((totals['energy'] / total) * 100),
                'color': '#8b5cf6'
            }
        ]
    
    @staticmethod
    def get_metrics(user_id, date_range='week'):
        """Get dashboard metrics"""
        start_date, end_date = DashboardService.get_date_range(date_range)
        
        current_totals = CarbonEmission.get_category_totals(user_id, start_date, end_date)
        
        # Get previous period for comparison
        period_days = (end_date - start_date).days
        previous_end_date = start_date - timedelta(days=1)
        previous_start_date = previous_end_date - timedelta(days=period_days)
        
        previous_totals = CarbonEmission.get_category_totals(
            user_id, previous_start_date, previous_end_date
        )
        
        # Calculate percentage change
        if previous_totals['total'] > 0:
            percent_change = round(
                ((current_totals['total'] - previous_totals['total']) / previous_totals['total']) * 100
            )
        else:
            percent_change = 0
        
        change_direction = '↓' if percent_change < 0 else '↑'
        
        total = current_totals['total'] if current_totals['total'] > 0 else 1
        
        return [
            {
                'label': 'Total CO₂',
                'value': f"{current_totals['total']:.1f} kg",
                'change': f"{change_direction} {abs(percent_change)}% vs last {date_range}",
                'icon': 'TrendingDown',
                'bgColor': 'bg-green-100',
                'iconColor': 'text-green-600'
            },
            {
                'label': 'Transport',
                'value': f"{current_totals['transport']:.1f} kg",
                'change': f"{round((current_totals['transport'] / total) * 100)}% of total",
                'icon': 'Activity',
                'bgColor': 'bg-blue-100',
                'iconColor': 'text-blue-600'
            },
            {
                'label': 'Food',
                'value': f"{current_totals['food']:.1f} kg",
                'change': f"{round((current_totals['food'] / total) * 100)}% of total",
                'icon': 'Leaf',
                'bgColor': 'bg-orange-100',
                'iconColor': 'text-orange-600'
            },
            {
                'label': 'Energy',
                'value': f"{current_totals['energy']:.1f} kg",
                'change': f"{round((current_totals['energy'] / total) * 100)}% of total",
                'icon': 'TrendingUp',
                'bgColor': 'bg-purple-100',
                'iconColor': 'text-purple-600'
            }
        ]
    
    @staticmethod
    def get_goal_progress(user_id):
        """Get goal progress"""
        user_goal = UserGoal.query.filter_by(user_id=user_id).first()
        
        if not user_goal:
            raise ValueError('User goals not found')
        
        # Get current week emissions
        now = datetime.now()
        week_start = (now - timedelta(days=7)).date()
        week_totals = CarbonEmission.get_category_totals(user_id, week_start, now.date())
        
        # Get current month emissions
        month_start = (now - timedelta(days=30)).date()
        month_totals = CarbonEmission.get_category_totals(user_id, month_start, now.date())
        
        week_progress = round((week_totals['total'] / user_goal.weekly_goal) * 100)
        month_progress = round((month_totals['total'] / user_goal.monthly_goal) * 100)
        
        return [
            {
                'label': f"Weekly Goal: {user_goal.weekly_goal} kg CO₂",
                'progress': week_progress,
                'remaining': f"{(user_goal.weekly_goal - week_totals['total']):.1f}",
                'color': 'emerald'
            },
            {
                'label': f"Monthly Goal: {user_goal.monthly_goal} kg CO₂",
                'progress': month_progress,
                'remaining': f"{(user_goal.monthly_goal - month_totals['total']):.1f}",
                'color': 'blue'
            }
        ]
    
    @staticmethod
    def get_comparison(user_id):
        """Get comparison with national average"""
        # Get user's average daily emissions (last 7 days)
        now = datetime.now()
        week_start = (now - timedelta(days=7)).date()
        week_totals = CarbonEmission.get_category_totals(user_id, week_start, now.date())
        user_average = round(week_totals['total'] / 7, 1)
        
        # Get national average (you can make this dynamic based on user's country)
        national_avg = NationalAverage.query.filter_by(country='USA').first()
        national_average = national_avg.average_daily if national_avg else 9.8
        
        percent_difference = round(((user_average - national_average) / national_average) * 100)
        is_below = percent_difference < 0
        
        return {
            'userAverage': user_average,
            'nationalAverage': national_average,
            'percentDifference': abs(percent_difference),
            'isBelow': is_below,
            'message': f"You are {abs(percent_difference)}% below average! 🎉" if is_below 
                      else f"You are {abs(percent_difference)}% above average"
        }
    
    @staticmethod
    def get_dashboard_summary(user_id, date_range='week'):
        """Get complete dashboard summary"""
        carbon_data = DashboardService.get_carbon_data(user_id, date_range)
        category_data = DashboardService.get_category_breakdown(user_id, date_range)
        metrics = DashboardService.get_metrics(user_id, date_range)
        goals = DashboardService.get_goal_progress(user_id)
        comparison = DashboardService.get_comparison(user_id)
        
        return {
            'carbonData': carbon_data,
            'categoryData': category_data,
            'metrics': metrics,
            'goals': goals,
            'comparison': comparison
        }
    
    @staticmethod
    def format_date(date, date_range):
        """Helper to format date based on range"""
        if date_range == 'day':
            return date.strftime('%H:%M')
        elif date_range == 'week':
            return date.strftime('%a')  # Mon, Tue, etc.
        elif date_range == 'month':
            return date.strftime('%b %d')  # Jan 01, etc.
        else:
            return date.strftime('%a')