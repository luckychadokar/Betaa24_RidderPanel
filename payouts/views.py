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
    """Auto-calculate weekly payout for a rider based on completed tasks"""
    from tasks.models import Task
    from datetime import timedelta, date
    from django.db.models import Sum

    rider = get_object_or_404(Rider, pk=rider_pk)

    if request.method == 'POST':
        week_start = request.POST.get('week_start')
        week_end = request.POST.get('week_end')

        tasks_in_week = Task.objects.filter(
            rider=rider, status='completed',
            task_date__gte=week_start, task_date__lte=week_end
        )
        total_earned = tasks_in_week.aggregate(t=Sum('earnings'))['t'] or 0
        task_count = tasks_in_week.count()

        # Check if a payout already exists for this exact week (avoid duplicate double-pay)
        already_paid = Payout.objects.filter(
            rider=rider, week_start=week_start, week_end=week_end
        ).aggregate(t=Sum('amount'))['t'] or 0

        amount_due = total_earned - already_paid

        if amount_due <= 0:
            messages.warning(request, f'No pending amount for this week. Already settled (₹{already_paid}).')
            return redirect('rider_payout_summary', pk=rider.pk)

        payout = Payout.objects.create(
            rider=rider,
            amount=amount_due,
            status='pending',
            payout_date=date.today(),
            week_start=week_start,
            week_end=week_end,
            note=f'Auto-calculated: {task_count} tasks completed in this week'
        )
        messages.success(
            request,
            f'Payout of ₹{amount_due} created for {rider.name} ({task_count} tasks, {week_start} to {week_end})'
        )
        return redirect('payout_list')

    # GET: show form with default current week (Mon-Sun)
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    return render(request, 'payouts/auto_calculate.html', {
        'rider': rider,
        'default_start': monday,
        'default_end': sunday,
    })