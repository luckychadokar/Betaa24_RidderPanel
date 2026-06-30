from django import forms
from .models import Payout


class PayoutForm(forms.ModelForm):
    class Meta:
        model = Payout
        fields = ["rider", "amount", "status", "payout_date", "week_start", "week_end", "note"]
        widgets = {
            "payout_date": forms.DateInput(attrs={"type": "date"}),
            "week_start": forms.DateInput(attrs={"type": "date"}),
            "week_end": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 2}),
        }

