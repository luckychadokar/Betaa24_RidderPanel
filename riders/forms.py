from django import forms
from .models import Rider, RiderTraining, RiderDocument, BankDetail


class RiderForm(forms.ModelForm):
    class Meta:
        model = Rider
        fields = ['beta_code', 'name', 'mobile', 'email', 'state', 'city', 'vehicle_type',
                  'joining_date', 'status', 'address', 'emergency_contact',
                  'profile_photo']
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }


class TrainingForm(forms.ModelForm):
    class Meta:
        model = RiderTraining
        fields = ['status', 'reason', 'reason_detail', 'training_date',
                  'alternate_number', 'location', 'state', 'city',
                  'training_done_by', 'final_remark']
        widgets = {
            'training_date': forms.DateInput(attrs={'type': 'date'}),
            'reason_detail': forms.Textarea(attrs={'rows': 2}),
            'final_remark': forms.Textarea(attrs={'rows': 2}),
        }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = RiderDocument
        fields = [
            'aadhaar_number', 'aadhaar_front', 'aadhaar_back', 'aadhaar_status',
            'dl_number', 'dl_front', 'dl_back', 'dl_status',
            'rc_number', 'rc_front', 'rc_status',
            'insurance_number', 'insurance_doc', 'insurance_expiry', 'insurance_status',
            'marksheet_doc', 'marksheet_status',
            'police_verification_doc', 'police_verification_status',
            'pan_number', 'pan_doc', 'pan_status',
            'overall_status',
        ]
        widgets = {
            'insurance_expiry': forms.DateInput(attrs={'type': 'date'}),
        }


class BankDetailForm(forms.ModelForm):
    class Meta:
        model = BankDetail
        fields = [
            'account_holder_name', 'account_number', 'account_number_confirm',
            'ifsc_code', 'bank_name', 'branch_name', 'account_type',
            'passbook_image', 'verify_status',
        ]

    def clean(self):
        cleaned = super().clean()
        acc1 = cleaned.get('account_number')
        acc2 = cleaned.get('account_number_confirm')
        if acc1 and acc2 and acc1 != acc2:
            raise forms.ValidationError('Account number and confirmation do not match.')
        return cleaned


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label='Upload Excel File (.xlsx)')