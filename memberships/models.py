from django.db import models
from django.contrib.auth.models import User


class Trainee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=250)
    dob = models.CharField(max_length=250, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    health_conditions = models.BooleanField(default=False)
    health_details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}"


class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.FileField(upload_to='trainer_profile', null=True, blank=True)
    phone_number = models.CharField(max_length=250)
    specialization = models.CharField(max_length=250)
    gender = models.CharField(max_length=10, null=True, blank=True)
    dob = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}"


class Appointment(models.Model):
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE, related_name='appointments')
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField()
    status = models.CharField(
        max_length=30,
        choices=(
            ('Cancelled', 'Cancelled'),
            ('Pending', 'Pending'),
            ('Rescheduled', 'Rescheduled'),
            ('Confirmed', 'Confirmed'),
            ('Completed', 'Completed'),
        ),
        default='Pending'
    )
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    payment_status = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True) 

    def __str__(self):
        return f'Appointment of {self.trainee.user.username} with {self.trainer.user.username} on {self.appointment_date}'


class Membership(models.Model):
    MEMBERSHIP_TYPES = (
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    )

    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE, related_name='memberships')
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True, related_name='memberships')

    # 🔑 Make appointment optional + SET_NULL so membership can exist before scheduling
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_memberships'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trainee.user.username} - {self.membership_type}"


class Billing(models.Model):
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE, related_name='billings')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='billings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_date = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Billing for {self.trainee.user.username} on {self.billing_date}"


class DietPlan(models.Model):
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True)
    plan_details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Diet Plan for {self.trainee.user.username} created on {self.created_at}"


class WorkoutPlan(models.Model):
    trainee = models.ForeignKey(Trainee, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True)
    plan_details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Workout Plan for {self.trainee.user.username} created on {self.created_at}"
