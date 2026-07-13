from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from .models import Task, calculate_earnings
from .forms import TaskForm
import openpyxl
from io import BytesIO
from .models import Task, calculate_earnings, CustomerWallet, CustomerRecharge
from .forms import TaskForm, CustomerWalletForm, CustomerRechargeForm
from django.http import HttpResponse, JsonResponse


@login_required
def task_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    tasks = Task.objects.select_related('rider').all()
    if q:
        tasks = tasks.filter(
            Q(task_id__icontains=q) |
            Q(customer_name__icontains=q) |
            Q(rider__name__icontains=q))
    if status:
        tasks = tasks.filter(status=status)
    if date_from:
        tasks = tasks.filter(task_date__gte=date_from)
    if date_to:
        tasks = tasks.filter(task_date__lte=date_to)
    return render(request, 'tasks/list.html', {
        'tasks': tasks, 'q': q, 'status': status})


@login_required
def task_add(request):
    form = TaskForm(request.POST or None)
    if form.is_valid():
        task = form.save()
        messages.success(request, f'Task {task.task_id} added!')
        return redirect('task_list')
    return render(request, 'tasks/form.html', {'form': form, 'title': 'Add Task'})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    form = TaskForm(request.POST or None, instance=task)
    if form.is_valid():
        form.save()
        messages.success(request, 'Task updated!')
        return redirect('task_list')
    return render(request, 'tasks/form.html', {
        'form': form, 'title': 'Edit Task', 'task': task})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    rows = [
        ('Customer Beta ID', task.customer_beta_id or '-'),
('Task Work ID', task.task_work_id or '-'),
        ('Rider', task.rider.name if task.rider else '-'),
        ('Task Type', task.get_task_type_display()),
        ('Task Date', task.task_date),
        ('No. of Tasks', task.num_tasks),
        ('Time Taken', f'{task.time_taken} min'),
        ('Distance', f'{task.distance_km} km'),
        ('Customer', task.customer_name or '-'),
        ('Customer Phone', task.customer_number or '-'),
        ('Pickup Address', task.pickup_address or '-'),
        ('Drop Address', task.drop_address or '-'),
        ('Remarks', task.remarks or '-'),
        ('Cancelled By', task.cancelled_by or '-'),
        ('Cancel Reason', task.cancellation_reason or '-'),
    ]
    return render(request, 'tasks/detail.html', {'task': task, 'rows': rows})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted.')
        return redirect('task_list')
    return render(request, 'tasks/confirm_delete.html', {'task': task})


@login_required
def cancelled_tasks(request):
    tasks = Task.objects.filter(status='cancelled').select_related('rider')
    by_rider = tasks.filter(cancelled_by='rider').count()
    by_customer = tasks.filter(cancelled_by='customer').count()
    by_company = tasks.filter(cancelled_by='company').count()
    return render(request, 'tasks/cancelled.html', {
        'tasks': tasks,
        'by_rider': by_rider,
        'by_customer': by_customer,
        'by_company': by_company,
    })


@login_required
def earnings_preview(request):
    try:
        n = int(request.GET.get('tasks', 1))
        t = int(request.GET.get('time', 10))
        d = float(request.GET.get('dist', 2))
        amount = calculate_earnings(n, t, d)
        return JsonResponse({'earnings': str(amount)})
    except Exception:
        return JsonResponse({'earnings': '24.50'})


@login_required
def task_export(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Tasks'
    ws.append(['Task ID', 'Rider', 'Customer', 'Date', 'Type',
               'Tasks', 'Time(min)', 'Distance(KM)', 'Earnings', 'Status'])
    for t in Task.objects.select_related('rider').all():
        ws.append([
            t.task_id,
            t.rider.name if t.rider else '',
            t.customer_name,
            str(t.task_date),
            t.task_type,
            t.num_tasks,
            t.time_taken,
            str(t.distance_km),
            str(t.earnings),
            t.status,
        ])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(
        buf,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=beta24_tasks.xlsx'
    return response

@login_required
def customer_wallet_list(request):
    wallets = CustomerWallet.objects.all()
    return render(request, 'tasks/customer_wallets.html', {'wallets': wallets})


@login_required
def customer_wallet_detail(request, pk):
    wallet = get_object_or_404(CustomerWallet, pk=pk)
    recharges = wallet.recharges.all()
    tasks = wallet.tasks.all()
    return render(request, 'tasks/customer_wallet_detail.html', {
        'wallet': wallet, 'recharges': recharges, 'tasks': tasks
    })


@login_required
def customer_wallet_add(request):
    form = CustomerWalletForm(request.POST or None)
    if form.is_valid():
        wallet = form.save()
        messages.success(request, f'Customer {wallet.customer_name} wallet created!')
        return redirect('customer_recharge', pk=wallet.pk)
    return render(request, 'tasks/customer_wallet_form.html', {
        'form': form, 'title': 'Add Customer'
    })


@login_required
def customer_recharge(request, pk):
    wallet = get_object_or_404(CustomerWallet, pk=pk)

    if request.method == 'POST':
        from decimal import Decimal
        tasks_added = int(request.POST.get('tasks_added', 0))
        minutes_added = int(request.POST.get('minutes_added', 0))
        km_added = Decimal(str(request.POST.get('km_added', 0)))
        amount_paid = Decimal(str(request.POST.get('amount_paid', 0)))
        note = request.POST.get('note', '')

        recharge = CustomerRecharge(
            wallet=wallet,
            recharge_type='manual',
            amount_paid=amount_paid,
            tasks_added=tasks_added,
            minutes_added=minutes_added,
            km_added=km_added,
            note=note,
        )
        recharge.save()
        messages.success(request, f'Recharge added! Tasks: +{tasks_added}, Min: +{minutes_added}, KM: +{km_added}')
        return redirect('customer_wallet_detail', pk=pk)

    return render(request, 'tasks/customer_recharge_form.html', {
        'wallet': wallet
    })

@login_required
def customer_wallet_api(request):
    """AJAX: get wallet info by mobile number"""
    mobile = request.GET.get('mobile', '')
    try:
        wallet = CustomerWallet.objects.get(customer_mobile=mobile)
        return JsonResponse({
            'found': True,
            'name': wallet.customer_name,
            'tasks': wallet.available_tasks,
            'minutes': wallet.available_minutes,
            'km': str(wallet.available_km),
            'wallet_id': wallet.pk,
        })
    except CustomerWallet.DoesNotExist:
        return JsonResponse({'found': False})