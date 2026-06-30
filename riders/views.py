from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q
from .models import Rider, RiderTraining, RiderDocument, WalletTransaction
from .forms import RiderForm, TrainingForm, DocumentForm, ExcelUploadForm
import openpyxl
from io import BytesIO
from .models import Rider, RiderTraining, RiderDocument, BankDetail, WalletTransaction
from .forms import RiderForm, TrainingForm, DocumentForm, BankDetailForm, ExcelUploadForm


@login_required
def rider_list(request):
    q = request.GET.get('q','')
    status = request.GET.get('status','')
    riders = Rider.objects.all()
    if q:
        riders = riders.filter(Q(name__icontains=q)|Q(mobile__icontains=q)|Q(city__icontains=q))
    if status:
        riders = riders.filter(status=status)
    dummy = Rider()
    return render(request, 'riders/list.html', {'riders': riders, 'q': q, 'status': status, 'rider': dummy})


@login_required
def rider_add(request):
    form = RiderForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        rider = form.save()
        RiderTraining.objects.get_or_create(rider=rider)
        RiderDocument.objects.get_or_create(rider=rider)
        messages.success(request, f'Rider {rider.name} added successfully!')
        return redirect('rider_list')
    return render(request, 'riders/form.html', {'form': form, 'title': 'Add Rider'})


@login_required
def rider_edit(request, pk):
    rider = get_object_or_404(Rider, pk=pk)
    form = RiderForm(request.POST or None, request.FILES or None, instance=rider)
    if form.is_valid():
        form.save()
        messages.success(request, 'Rider updated!')
        return redirect('rider_detail', pk=pk)
    return render(request, 'riders/form.html', {'form': form, 'title': 'Edit Rider', 'rider': rider})


@login_required
def rider_detail(request, pk):
    rider = get_object_or_404(Rider, pk=pk)
    training = getattr(rider, 'training', None)
    docs = getattr(rider, 'documents', None)
    tasks = rider.tasks.all()[:10]
    txns = rider.wallet_transactions.all()[:10]
    doc_status = []
    if docs:
        doc_status = [
            ('Aadhaar', docs.aadhaar_status),
            ('PAN', docs.pan_status),
            ('Driving License', docs.dl_status),
            ('Overall', docs.overall_status),
        ]
    wallet_rows = [
        ('Total Earned', rider.total_earnings, 'text-g'),
        ('Total Paid', rider.total_paid, 'text-g'),
        ('Pending', rider.pending_amount, 'text-r'),
    ]
    return render(request, 'riders/detail.html', {
        'rider': rider, 'training': training, 'docs': docs,
        'tasks': tasks, 'txns': txns, 'doc_status': doc_status,
        'wallet_rows': wallet_rows,
    })


@login_required
def rider_delete(request, pk):
    rider = get_object_or_404(Rider, pk=pk)
    if request.method == 'POST':
        rider.delete()
        messages.success(request, 'Rider deleted.')
        return redirect('rider_list')
    return render(request, 'riders/confirm_delete.html', {'obj': rider, 'type': 'Rider'})


@login_required
def training_update(request, pk):
    rider = get_object_or_404(Rider, pk=pk)
    training, _ = RiderTraining.objects.get_or_create(rider=rider)
    form = TrainingForm(request.POST or None, instance=training)
    if form.is_valid():
        form.save()
        messages.success(request, 'Training status updated!')
        return redirect('rider_detail', pk=pk)
    return render(request, 'riders/training_form.html', {'form': form, 'rider': rider})


@login_required
def document_update(request, pk):
    rider = get_object_or_404(Rider, pk=pk)
    doc, _ = RiderDocument.objects.get_or_create(rider=rider)
    form = DocumentForm(request.POST or None, request.FILES or None, instance=doc)
    if form.is_valid():
        form.save()
        messages.success(request, 'Documents updated!')
        return redirect('rider_detail', pk=pk)
    return render(request, 'riders/doc_form.html', {'form': form, 'rider': rider})


@login_required
def excel_import(request):
    form = ExcelUploadForm(request.POST or None, request.FILES or None)
    imported, errors, skipped = [], [], []

    # Possible column name variations -> our field name
    COLUMN_MAP = {
        'name': ['name', 'rider name', 'full name', 'rider_name', 'fullname', 'riders name'],
        'mobile': ['mobile', 'phone', 'mobile number', 'mobile no', 'phone number',
                   'contact', 'contact number', 'mobile_number', 'phone_number', 'number'],
        'email': ['email', 'email id', 'email address', 'mail', 'e-mail'],
        'city': ['city', 'location', 'town', 'area'],
        'vehicle_type': ['vehicle_type', 'vehicle', 'vehicle type', 'bike type', 'vehicletype'],
        'status': ['status', 'rider status', 'state'],
        'joining_date': ['joining_date', 'joining date', 'join date', 'date of joining',
                          'doj', 'joined on', 'joiningdate'],
        'address': ['address', 'full address', 'residential address'],
        'emergency_contact': ['emergency_contact', 'emergency contact', 'emergency number',
                               'alternate number', 'alternate contact'],
        'rating': ['rating', 'rider rating', 'stars'],
    }

    def normalize(s):
        return str(s).strip().lower().replace('_', ' ').replace('-', ' ') if s else ''

    def build_header_index(headers):
        """Map our field name -> column index, based on fuzzy matching"""
        norm_headers = [normalize(h) for h in headers]
        field_index = {}
        for field, variations in COLUMN_MAP.items():
            for idx, h in enumerate(norm_headers):
                if h in [normalize(v) for v in variations]:
                    field_index[field] = idx
                    break
        return field_index

    def get_val(row, field_index, field, default=''):
        idx = field_index.get(field)
        if idx is None or idx >= len(row):
            return default
        val = row[idx]
        return str(val).strip() if val is not None else default

    def clean_mobile(raw):
        """Extract digits only, handle floats like 9876543210.0, +91 prefix etc."""
        if not raw:
            return ''
        s = str(raw).strip()
        if s.endswith('.0'):
            s = s[:-2]
        digits = ''.join(ch for ch in s if ch.isdigit())
        if len(digits) > 10:
            digits = digits[-10:]  # keep last 10 digits (strip country code)
        return digits

    def map_status(raw):
        if not raw:
            return 'new'
        s = normalize(raw)
        mapping = {
            'new': 'new', 'active': 'active', 'inactive': 'inactive',
            'training pending': 'training_pending', 'pending training': 'training_pending',
            'documents pending': 'documents_pending', 'docs pending': 'documents_pending',
            'ready': 'ready', 'ready for activation': 'ready',
        }
        return mapping.get(s, 'new')

    if form.is_valid():
        try:
            excel_file = request.FILES['excel_file']
            wb = openpyxl.load_workbook(excel_file, data_only=True)
            ws = wb.active

            rows_iter = ws.iter_rows(values_only=True)
            try:
                header_row = next(rows_iter)
            except StopIteration:
                errors.append('Excel file is empty.')
                header_row = None

            if header_row:
                headers = [str(h) if h is not None else '' for h in header_row]
                field_index = build_header_index(headers)

                if 'mobile' not in field_index:
                    errors.append(
                        'Could not find a Mobile/Phone column in the file. '
                        'Please make sure one column is named like "Mobile", "Phone", or "Contact Number".'
                    )
                else:
                    for row_num, row in enumerate(rows_iter, start=2):
                        if row is None or all(c is None for c in row):
                            continue

                        mobile_raw = get_val(row, field_index, 'mobile')
                        mobile = clean_mobile(mobile_raw)

                        if not mobile or len(mobile) != 10:
                            skipped.append({
                                'row': row_num,
                                'reason': f'Invalid/missing mobile number ("{mobile_raw}")'
                            })
                            continue

                        name = get_val(row, field_index, 'name') or f'Rider {mobile}'
                        email = get_val(row, field_index, 'email')
                        city = get_val(row, field_index, 'city') or 'Bhopal'
                        vehicle = get_val(row, field_index, 'vehicle_type') or 'Bike'
                        status_raw = get_val(row, field_index, 'status')
                        status = map_status(status_raw)
                        address = get_val(row, field_index, 'address')
                        emergency = clean_mobile(get_val(row, field_index, 'emergency_contact'))

                        try:
                            rider, created = Rider.objects.update_or_create(
                                mobile=mobile,
                                defaults={
                                    'name': name,
                                    'email': email,
                                    'city': city,
                                    'vehicle_type': vehicle,
                                    'status': status,
                                    'address': address,
                                    'emergency_contact': emergency,
                                }
                            )
                            if created:
                                RiderTraining.objects.get_or_create(rider=rider)
                                RiderDocument.objects.get_or_create(rider=rider)
                            imported.append({
                                'name': rider.name,
                                'mobile': rider.mobile,
                                'action': 'Created' if created else 'Updated'
                            })
                        except Exception as e:
                            skipped.append({'row': row_num, 'reason': str(e)})

        except Exception as e:
            errors.append(f'File could not be processed: {e}')

    return render(request, 'riders/excel_import.html', {
        'form': form,
        'imported': imported,
        'errors': errors,
        'skipped': skipped,
    })


@login_required
def excel_export(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Riders'
    ws.append(['ID','Name','Mobile','Email','City','Vehicle','Status','Rating','Total Tasks','Total Earnings','Joined'])
    for r in Rider.objects.all():
        ws.append([r.id, r.name, r.mobile, r.email, r.city, r.vehicle_type, r.status,
                   str(r.rating), r.total_tasks, str(r.total_earnings), str(r.joining_date)])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename=beta24_riders.xlsx'
    return resp
@login_required
def bank_detail_update(request, pk):
    rider = get_object_or_404(Rider, pk=pk)
    bank, _ = BankDetail.objects.get_or_create(rider=rider)
    form = BankDetailForm(request.POST or None, request.FILES or None, instance=bank)
    if form.is_valid():
        form.save()
        messages.success(request, 'Bank details updated!')
        return redirect('rider_detail', pk=pk)
    return render(request, 'riders/bank_form.html', {'form': form, 'rider': rider})


@login_required
def ifsc_lookup(request):
    """AJAX endpoint: given IFSC code, fetch bank name and branch using free Razorpay IFSC API"""
    import requests
    ifsc = request.GET.get('ifsc', '').strip().upper()
    if len(ifsc) != 11:
        return JsonResponse({'error': 'Invalid IFSC code length'}, status=400)
    try:
        resp = requests.get(f'https://ifsc.razorpay.com/{ifsc}', timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return JsonResponse({
                'bank_name': data.get('BANK', ''),
                'branch_name': data.get('BRANCH', ''),
                'city': data.get('CITY', ''),
            })
        else:
            return JsonResponse({'error': 'IFSC not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def training_records(request):
    q = request.GET.get('q', '')
    records = RiderTraining.objects.select_related('rider').all().order_by('-updated_at')
    if q:
        records = records.filter(
            Q(rider__name__icontains=q) |
            Q(rider__mobile__icontains=q) |
            Q(location__icontains=q) |
            Q(city__icontains=q)
        )
    return render(request, 'riders/training_records.html', {'records': records, 'q': q})

@login_required
def training_import(request):
    """Import training records from pasted tab-separated data:
    Date | Name | Number | Alternate Number | Location | State | City | Training Done By | Final Remark
    """
    imported, skipped = [], []

    if request.method == 'POST':
        raw_text = request.POST.get('raw_data', '').strip()
        if raw_text:
            lines = [l for l in raw_text.split('\n') if l.strip()]
            for line_num, line in enumerate(lines, start=1):
                parts = line.split('\t')
                parts = [p.strip() for p in parts]

                if len(parts) < 3:
                    skipped.append({'row': line_num, 'reason': 'Too few columns', 'raw': line[:60]})
                    continue

                try:
                    date_str = parts[0] if len(parts) > 0 else ''
                    name = parts[1] if len(parts) > 1 else ''
                    mobile_raw = parts[2] if len(parts) > 2 else ''
                    alt_number = parts[3] if len(parts) > 3 and parts[3].lower() != 'na' else ''
                    location = parts[4] if len(parts) > 4 else ''
                    state = parts[5] if len(parts) > 5 else ''
                    city = parts[6] if len(parts) > 6 else ''
                    done_by = parts[7] if len(parts) > 7 else ''
                    remark = parts[8] if len(parts) > 8 else ''

                    mobile = ''.join(ch for ch in mobile_raw if ch.isdigit())[-10:]

                    if not mobile or len(mobile) != 10:
                        skipped.append({'row': line_num, 'reason': f'Invalid mobile: {mobile_raw}', 'raw': line[:60]})
                        continue

                    # Find rider by mobile, or create a minimal one if not found
                    rider, created = Rider.objects.get_or_create(
                        mobile=mobile,
                        defaults={'name': name or f'Rider {mobile}', 'city': city or 'Bhopal'}
                    )
                    if created:
                        RiderDocument.objects.get_or_create(rider=rider)

                    # Determine training status from remark
                    remark_lower = remark.strip().lower()
                    if 'done' in remark_lower:
                        status = 'completed'
                    elif remark_lower in ('npc', 'not intrested', 'not interested'):
                        status = 'rejected'
                    elif remark_lower:
                        status = 'pending'  # has a remark but not clearly done
                    else:
                        status = 'pending'

                    # Parse date
                    from datetime import datetime
                    training_date = None
                    for fmt in ('%d-%b-%Y', '%d-%b-%y', '%d %b %Y', '%d/%m/%Y'):
                        try:
                            training_date = datetime.strptime(date_str, fmt).date()
                            break
                        except (ValueError, TypeError):
                            continue

                    training, _ = RiderTraining.objects.update_or_create(
                        rider=rider,
                        defaults={
                            'status': status,
                            'alternate_number': alt_number,
                            'location': location,
                            'state': state,
                            'city': city,
                            'training_done_by': done_by,
                            'final_remark': remark,
                            'training_date': training_date,
                        }
                    )

                    imported.append({
                        'name': rider.name,
                        'mobile': rider.mobile,
                        'status': status,
                        'remark': remark,
                    })
                except Exception as e:
                    skipped.append({'row': line_num, 'reason': str(e), 'raw': line[:60]})

    return render(request, 'riders/training_import.html', {
        'imported': imported,
        'skipped': skipped,
    })