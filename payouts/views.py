from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum
from riders.models import Rider, WalletTransaction
from .models import Payout
from .forms import PayoutForm
import openpyxl
from io import BytesIO


@login_required
def payout_list(request):
    payouts = Payout.objects.select_related('rider').all()
    total_paid = payouts.filter(status='paid').aggregate(
        t=Sum('amount'))['t'] or 0
    total_pending = payouts.filter(status='pending').aggregate(
        t=Sum('amount'))['t'] or 0
    return render(request, 'payouts/list.html', {
        'payouts': payouts,
        'total_paid': total_paid,
        'total_pending': total_pending,
    })


@login_required
def payout_add(request):
    form = PayoutForm(request.POST or None)
    if form.is_valid():
        payout = form.save()
        if payout.status == 'paid':
            WalletTransaction.objects.create(
                rider=payout.rider, txn_type='debit',
                amount=payout.amount,
                description=f'Payout on {payout.payout_date}')
            payout.rider.wallet_balance -= payout.amount
            payout.rider.save(update_fields=['wallet_balance'])
        messages.success(request, 'Payout recorded!')
        return redirect('payout_list')
    return render(request, 'payouts/form.html', {
        'form': form, 'title': 'Add Payout'})


@login_required
def payout_mark_paid(request, pk):
    payout = get_object_or_404(Payout, pk=pk)
    if payout.status != 'paid':
        payout.status = 'paid'
        payout.save()
        WalletTransaction.objects.create(
            rider=payout.rider, txn_type='debit',
            amount=payout.amount,
            description=f'Payout #{payout.id}')
        payout.rider.wallet_balance -= payout.amount
        payout.rider.save(update_fields=['wallet_balance'])
        messages.success(
            request,
            f'₹{payout.amount} marked as paid for {payout.rider.name}')
    return redirect('payout_list')


@login_required
def rider_payout_summary(request, pk):
    rider = get_object_or_404(Rider, pk=pk)
    payouts = rider.payouts.all()
    txns = rider.wallet_transactions.all()
    return render(request, 'payouts/rider_summary.html', {
        'rider': rider, 'payouts': payouts, 'txns': txns})


@login_required
def payout_export(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Payouts'
    ws.append(['Rider', 'Amount', 'Status', 'Date', 'Week Start', 'Week End', 'Note'])
    for p in Payout.objects.select_related('rider').all():
        ws.append([
            p.rider.name, str(p.amount), p.status,
            str(p.payout_date),
            str(p.week_start or ''),
            str(p.week_end or ''),
            p.note,
        ])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(
        buf,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=beta24_payouts.xlsx'
    return response

@login_required
def auto_calculate_payout(request, rider_pk):
    from tasks.models import Task
    from datetime import timedelta, date
    from django.db.models import Sum
    from decimal import Decimal

    rider = get_object_or_404(Rider, pk=rider_pk)

    if request.method == 'POST':
        week_start = request.POST.get('week_start')
        week_end = request.POST.get('week_end')
        attendance_days = int(request.POST.get('attendance_days', 0))

        # Task earnings
        tasks_in_week = Task.objects.filter(
            rider=rider, status='completed',
            task_date__gte=week_start, task_date__lte=week_end
        )
        task_amount = tasks_in_week.aggregate(t=Sum('earnings'))['t'] or Decimal('0')
        task_count = tasks_in_week.count()

        # Login/Attendance bonus
        login_amount = Decimal(attendance_days * 50)

        # Total before TDS
        total_amount = task_amount + login_amount

        # TDS @ 2%
        tds = round(total_amount * Decimal('0.02'), 2)

        # Net payout
        net_payout = round(total_amount - tds, 2)

        # Already paid check
        already_paid = Payout.objects.filter(
            rider=rider, week_start=week_start, week_end=week_end
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

        if net_payout <= already_paid:
            messages.warning(
                request,
                f'No pending amount. Already settled (₹{already_paid}).'
            )
            return redirect('rider_payout_summary', pk=rider.pk)

        # Bank details
        bank = getattr(rider, 'bank_detail', None)
        docs = getattr(rider, 'documents', None)

        payout = Payout.objects.create(
            rider=rider,
            amount=net_payout,
            status='pending',
            payout_date=date.today(),
            week_start=week_start,
            week_end=week_end,
            note=(
                f'Tasks: {task_count} | Task Amount: ₹{task_amount} | '
                f'Login Amount: ₹{login_amount} ({attendance_days} days×₹50) | '
                f'Total: ₹{total_amount} | TDS(2%): ₹{tds} | Net Pay: ₹{net_payout}'
            )
        )
        messages.success(
            request,
            f'Payout ₹{net_payout} created for {rider.name} '
            f'(Task ₹{task_amount} + Login ₹{login_amount} - TDS ₹{tds})'
        )
        return redirect('payout_list')

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    # Get bank and doc details for preview
    bank = getattr(rider, 'bank_detail', None)
    docs = getattr(rider, 'documents', None)

    return render(request, 'payouts/auto_calculate.html', {
        'rider': rider,
        'default_start': monday,
        'default_end': sunday,
        'bank': bank,
        'docs': docs,
    })
    
    # GET — default current week Mon-Sun
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    return render(request, 'payouts/auto_calculate.html', {
        'rider': rider,
        'default_start': monday,
        'default_end': sunday,
    })

from django.http import JsonResponse

@login_required
def payout_preview(request):
    """AJAX: return task earnings for a rider in a date range"""
    from tasks.models import Task
    from django.db.models import Sum
    rider_pk = request.GET.get('rider')
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    try:
        earnings = Task.objects.filter(
            rider_id=rider_pk, status='completed',
            task_date__gte=date_from, task_date__lte=date_to
        ).aggregate(t=Sum('earnings'))['t'] or 0
        return JsonResponse({'earnings': float(earnings)})
    except Exception as e:
        return JsonResponse({'earnings': 0})