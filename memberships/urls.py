from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('trainer/dashboard/', views.trainer_dashboard, name='trainer_dashboard'),
    path('trainee/dashboard/', views.trainee_dashboard, name='trainee_dashboard'),
    path('membership/plans/', views.membership_plans, name='membership_plans'),
    path('appointment/book/', views.book_appointment, name='book_appointment'),
    path('appointments/view/', views.view_appointments, name='view_appointments'),

    path('billing/info/', views.billing_info, name='billing_info'),
    path('profile/', views.trainee_profile, name='trainee_profile'),
    path('membership/details/', views.membership_details, name='membership_details'),
    path('trainers/', views.trainer_list, name='trainer_list'),
    path('trainees/', views.trainee_list, name='trainee_list'),

    path('membership/checkout/<str:plan_type>/', views.membership_checkout, name='membership_checkout'),
    path('membership/payment-success/<int:membership_id>/', views.membership_payment_success, name='membership_payment_success'),

    path('appointment/book/', views.book_appointment, name='book_appointment'),

    path('register/trainer/', views.register_trainer, name='register_trainer'),
    path('register/trainee/', views.register_trainee, name='register_trainee'),

    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),

]