from django.urls import path
from . import views

urlpatterns = [
    path('deposit/', views.deposit, name='deposit'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('transfer/', views.transfer, name='transfer'),
    path('history/', views.transaction_history, name='history'),
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('download-statement/', views.download_statement, name='download_statement'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('verify-transfer-otp/', views.verify_transfer_otp, name='verify_transfer_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
]