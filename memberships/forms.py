from django import forms
from .models import Trainer, Membership


class MembershipChoiceForm(forms.Form):
    MEMBERSHIP_CHOICES = Membership.MEMBERSHIP_TYPES

    DURATION_CHOICES = (
        (1, '1 Month'),
        (3, '3 Months'),
        (6, '6 Months'),
        (12, '12 Months'),
    )

    membership_type = forms.ChoiceField(
        choices=MEMBERSHIP_CHOICES,
        widget=forms.RadioSelect,
        label="Choose Membership"
    )
    duration_months = forms.ChoiceField(
        choices=DURATION_CHOICES,
        label="Duration"
    )


class TrainerChoiceForm(forms.Form):
    trainer = forms.ModelChoiceField(
        queryset=Trainer.objects.all(),
        label="Choose Trainer",
        empty_label="Select a trainer"
    )
    def __init__(self, *args, **kwargs):
        super(TrainerChoiceForm, self).__init__(*args, **kwargs)
        self.fields['trainer'].queryset = Trainer.objects.all()