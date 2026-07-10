from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from riders.models import Rider
from tasks.models import Task
from payouts.models import Payout
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache



@never_cache
@login_required
def dashboard(request):
    today = timezone.now().date()
    from datetime import timedelta

    riders = Rider.objects.all()
    tasks = Task.objects.all()

    total_riders = riders.count()
    active_riders = riders.filter(status='active').count()
    training_pending = riders.filter(status='training_pending').count()
    docs_pending = riders.filter(status='documents_pending').count()

    total_tasks = tasks.count()
    today_tasks = tasks.filter(task_date=today).count()
    completed_tasks = tasks.filter(status='completed').count()
    cancelled_tasks = tasks.filter(status='cancelled').count()

    today_earnings = tasks.filter(task_date=today, status='completed').aggregate(
        t=Sum('earnings'))['t'] or 0
    total_earnings = tasks.filter(status='completed').aggregate(
        t=Sum('earnings'))['t'] or 0

    pending_payout = Payout.objects.filter(status='pending').aggregate(
        t=Sum('amount'))['t'] or 0
    total_paid = Payout.objects.filter(status='paid').aggregate(
        t=Sum('amount'))['t'] or 0

    # Last 7 days chart data
    chart_labels, chart_earnings, chart_tasks = [], [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        chart_labels.append(d.strftime('%a'))
        e = tasks.filter(task_date=d, status='completed').aggregate(
            t=Sum('earnings'))['t'] or 0
        chart_earnings.append(float(e))
        chart_tasks.append(tasks.filter(task_date=d).count())

    top_riders = Rider.objects.annotate(
    total_earned=Sum('tasks__earnings', filter=Q(tasks__status='completed'))
).filter(total_earned__gt=0).order_by('-total_earned')[:5]
    recent_tasks = Task.objects.select_related('rider').order_by('-created_at')[:8]

    return render(request, 'dashboard.html', {
        'total_riders': total_riders,
        'active_riders': active_riders,
        'training_pending': training_pending,
        'docs_pending': docs_pending,
        'total_tasks': total_tasks,
        'today_tasks': today_tasks,
        'completed_tasks': completed_tasks,
        'cancelled_tasks': cancelled_tasks,
        'today_earnings': today_earnings,
        'total_earnings': total_earnings,
        'pending_payout': pending_payout,
        'total_paid': total_paid,
        'chart_labels': json.dumps(chart_labels),
        'chart_earnings': json.dumps(chart_earnings),
        'chart_tasks': json.dumps(chart_tasks),
        'top_riders': top_riders,
        'recent_tasks': recent_tasks,
    })