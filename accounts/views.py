import time

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db import transaction as db_transaction
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal
import random
from django.db.models import F
from .models import Account, Transaction, OTP
from .forms import RegisterForm


# ==========================
# 🔹 DEPOSIT
# ==========================
@login_required
def deposit(request):
    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get('amount', 0))

            if amount <= 0:
                messages.error(request, "Enter valid amount")
                return redirect('deposit')
            
            account = Account.objects.get(user=request.user)

            print("DEPOSIT ACCOUNT ID:", account.id)
            print("DEPOSIT BALANCE BEFORE:", account.balance)
            print("RAW AMOUNT:", request.POST.get('amount'))
            print("PARSED AMOUNT:", amount)

            # ✅ FIX HERE
            Account.objects.filter(user=request.user).update(
            balance=F('balance') + amount
)

            account.save()
            account.refresh_from_db()

            print("AFTER SAVE:", account.balance)

            Transaction.objects.create(
                account=account,
                amount=amount,
                transaction_type='DEPOSIT'
            )

            messages.success(request, "Deposit successful!", extra_tags='sound-deposit')
            return redirect('dashboard')
            

        except Exception as e:
            print("ERROR:", e)
            messages.error(request, "Something went wrong")
            return redirect('deposit')

    return render(request, 'deposit.html')
# ==========================
# 🔹 WITHDRAW
# ==========================
@login_required
def withdraw(request):
    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get('amount', 0))

            if amount <= 0:
                messages.error(request, "Enter valid amount", extra_tags='sound-error')
                return redirect('withdraw')

            account = Account.objects.get(user=request.user)

            if account.balance < amount:
                messages.error(request, "Insufficient balance", extra_tags='sound-error')
                return redirect('withdraw')

            Account.objects.filter(user=request.user).update(
                balance=F('balance') - amount
            )

            # ✅ Refresh updated balance
            account.refresh_from_db()

            Transaction.objects.create(
                account=account,
                amount=amount,
                transaction_type='WITHDRAW'
            )

            messages.success(
                request,
                f"₹{amount} withdrawn successfully!",
                extra_tags='sound-withdraw'
            )

            return redirect('dashboard')

        except Exception as e:
            print("ERROR:", e)
            messages.error(request, "Something went wrong", extra_tags='sound-error')
            return redirect('withdraw')

    return render(request, 'withdraw.html')

# ==========================
# 🔹 TRANSFER (OTP SEND)
# ==========================
@login_required
def transfer(request):
    if request.method == "POST":
        try:
            receiver_acc_no = request.POST.get('account_number')
            amount = Decimal(request.POST.get('amount', 0))

            sender = Account.objects.get(user=request.user)

            if amount <= 0:
             messages.error(request, "Enter valid amount", extra_tags='sound-error')
             return redirect('transfer')

            if sender.account_number == receiver_acc_no:
             messages.error(request, "Cannot transfer to yourself", extra_tags='sound-error')
             return redirect('transfer')

            if sender.balance < amount:
             messages.error(request, "Insufficient balance", extra_tags='sound-error')
             return redirect('transfer')

            otp = str(random.randint(100000, 999999))

            request.session['transfer_otp'] = otp
            request.session['receiver'] = receiver_acc_no
            request.session['amount'] = str(amount)
            
            request.session['otp_time'] = time.time()
            # print("Transfer OTP:", otp)
            
            messages.success(request, "OTP Sent!", extra_tags='sound-otp')
            return redirect('verify_transfer_otp')

        except Exception as e:
            print("ERROR:", e)
            messages.error(request, "Something went wrong", extra_tags='sound-error')
            return redirect('transfer')

    return render(request, 'transfer.html')
# ==========================
# 🔹 VERIFY TRANSFER OTP
# ==========================
@login_required
def verify_transfer_otp(request):
    real_otp = request.session.get('transfer_otp')
    otp_time = request.session.get('otp_time')

    if not real_otp or not otp_time:
        messages.error(request, "OTP expired. Try again.", extra_tags='sound-error')
        return redirect('transfer')

    if request.method == "POST":
        entered_otp = request.POST.get('otp')

        # ⏰ Check expiry HERE
        if time.time() - otp_time > 60:
            request.session.pop('transfer_otp', None)
            request.session.pop('receiver', None)
            request.session.pop('amount', None)
            request.session.pop('otp_time', None)

            messages.error(request, "OTP expired (60 sec). Try again.", extra_tags='sound-error')
            return redirect('transfer')

        if str(entered_otp) == str(real_otp):

            receiver_acc_no = request.session.get('receiver')
            amount = Decimal(request.session.get('amount', '0'))

            sender = Account.objects.get(user=request.user)

            try:
                receiver = Account.objects.get(account_number=receiver_acc_no)
            except Account.DoesNotExist:
                messages.error(request, "Receiver not found", extra_tags='sound-error')
                return redirect('transfer')

            if sender.balance < amount:
                messages.error(request, "Insufficient balance")
                return redirect('transfer')

            with db_transaction.atomic():
                Account.objects.filter(id=sender.id).update(
                    balance=F('balance') - amount
                )

                Account.objects.filter(id=receiver.id).update(
                    balance=F('balance') + amount
                )

            Transaction.objects.create(
                account=sender,
                sender=sender,
                receiver=receiver,
                amount=amount,
                transaction_type='TRANSFER_SENT'
            )

            Transaction.objects.create(
                account=receiver,
                sender=sender,
                receiver=receiver,
                amount=amount,
                transaction_type='TRANSFER_RECEIVED'
            )

            # Clear session
            request.session.pop('transfer_otp', None)
            request.session.pop('receiver', None)
            request.session.pop('amount', None)
            request.session.pop('otp_time', None)

            messages.success(request, "Transfer successful!", extra_tags='sound-transfer')
            return redirect('dashboard')

        else:
            messages.error(request, "Invalid OTP", extra_tags='sound-error')
            return redirect('verify_transfer_otp')

    return render(request, 'verify_transfer_otp.html', {
        'otp': real_otp
    })
# ==========================
# 🔹 DASHBOARD
# ==========================
@login_required
def dashboard(request):
    account = Account.objects.get(user=request.user)
    
    print("DASHBOARD ACCOUNT ID:", account.id)
    print("DASHBOARD BALANCE:", account.balance)

    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:5]

    return render(request, 'dashboard.html', {
        'account': account,
        'transactions': transactions
    })


# ==========================
# 🔹 TRANSACTION HISTORY
# ==========================
@login_required
def transaction_history(request):
    account = Account.objects.get(user=request.user)

    # ✅ FIXED QUERY
    transactions = Transaction.objects.filter(
        Q(sender=account) | Q(receiver=account)
    ).order_by('-timestamp')

    search = request.GET.get('search', '')
    t_type = request.GET.get('type', '')
    date = request.GET.get('date', '')

    if t_type:
        transactions = transactions.filter(transaction_type=t_type)

    if search:
        query = Q(transaction_type__icontains=search)

        query |= Q(sender__user__username__icontains=search)
        query |= Q(receiver__user__username__icontains=search)

        if search.isdigit():
            query |= Q(amount=Decimal(search))
            

        transactions = transactions.filter(query)

    if date:
        transactions = transactions.filter(timestamp__date=date)

    paginator = Paginator(transactions, 5)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    return render(request, 'history.html', {
        'transactions': transactions
    })


# ==========================
# 🔹 REGISTER
# ==========================
import random
from django.contrib.auth.models import User
import random

def register(request):
    if request.method == "POST":
        print("REGISTER VIEW HIT")

        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # 🔴 Password check
        if password1 != password2:
            print("PASSWORD MISMATCH ❌")
            return render(request, 'register.html', {
                'error': 'Passwords do not match'
            })

        # 🔴 Username check
        if User.objects.filter(username=username).exists():
            print("USERNAME EXISTS ❌")
            return render(request, 'register.html', {
                'error': 'Username already exists'
            })

        # ✅ Create user
        user = User.objects.create_user(username=username, password=password1)
        user.is_active = False
        user.save()

        # ✅ Generate OTP
        otp = random.randint(100000, 999999)
        OTP.objects.create(user=user, otp=otp)

        request.session['user_id'] = user.id

        print("OTP:", otp)

        return redirect('verify_otp')

    return render(request, 'register.html')

# ==========================
# 🔹 LOGIN
# ==========================
from django.contrib.auth import authenticate, login
from django.contrib import messages
def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(
                    request,
                    "Account not verified. Please verify OTP first.",
                    extra_tags='sound-error'
                )
            else:
                login(request, user)
                return redirect('dashboard')

        else:
            messages.error(
                request,
                "Invalid username or password",
                extra_tags='sound-error'
            )

    return render(request, 'login.html')
# ==========================
# 🔹 LOGOUT
# ==========================
def user_logout(request):
    logout(request)
    return redirect('login')


# ==========================
# 🔹 VERIFY REGISTER OTP
# ==========================

def verify_otp(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('register')

    from django.contrib.auth.models import User
    from django.contrib import messages

    user = User.objects.get(id=user_id)

    otp_obj = OTP.objects.filter(user=user).order_by('-created_at').first()

    if not otp_obj:
        return redirect('register')

    if request.method == "POST":
        entered_otp = request.POST.get('otp')

        if str(entered_otp) == str(otp_obj.otp):
            user.is_active = True
            user.save()

            # request.session.pop('user_id', None)

            messages.success(request, "Account created successfully! Please login.")

            return redirect('login')
        else:
            return render(request, 'verify_otp.html', {
                'error': 'Invalid OTP',
                'otp': otp_obj.otp
            })

    return render(request, 'verify_otp.html', {
        'otp': otp_obj.otp
    })
# ==========================
# 🔹 DOWNLOAD PDF
# ==========================
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.contrib.staticfiles import finders
from django.utils import timezone

@login_required
def download_statement(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="bank_statement.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    account = Account.objects.get(user=request.user)
    transactions = Transaction.objects.filter(account=account).order_by('timestamp')

    # ================= HEADER =================
    p.setFillColor(colors.HexColor("#0B3C5D"))
    p.rect(0, height - 80, width, 80, fill=1)

    # ================= LOGO =================
    logo_path = finders.find('images/bank_logo.png')

    if logo_path:
        p.drawImage(logo_path, 20, height - 75, width=65, height=65, mask='auto')

    # ================= HEADER TEXT =================
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(100, height - 40, "MY BANK")

    p.setFont("Helvetica", 9)
    p.drawString(100, height - 60, "Account Statement")

    # ================= WATERMARK =================
    p.saveState()
    p.setFont("Helvetica-Bold", 60)
    p.setFillColor(colors.Color(0.8, 0.8, 0.8, alpha=0.2))
    p.translate(width / 2, height / 2)
    p.rotate(45)
    p.drawCentredString(0, 0, "MY BANK")
    p.restoreState()

    # ================= IST TIME =================
    ist_now = timezone.localtime(timezone.now())

    p.setFillColor(colors.black)
    p.setFont("Helvetica", 9)

    p.drawString(40, height - 110, f"Account Holder: {request.user.username}")
    p.drawString(40, height - 125, f"Account Number: {account.account_number}")

    p.drawRightString(width - 40, height - 110, f"Date: {ist_now.strftime('%d-%m-%Y')}")
    p.drawRightString(width - 40, height - 125, f"Time: {ist_now.strftime('%I:%M %p')}")

    # ================= TABLE HEADER =================
    y = height - 180

    p.setFillColor(colors.HexColor("#1E5F8B"))
    p.rect(40, y, width - 80, 25, fill=1)

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 10)

    p.drawString(50, y + 7, "Date")
    p.drawString(110, y + 7, "Time")
    p.drawString(180, y + 7, "Type")
    p.drawString(270, y + 7, "Debit")
    p.drawString(360, y + 7, "Credit")
    p.drawString(450, y + 7, "Balance")

    y -= 30

    # ================= TRANSACTIONS =================
    running_balance = 0

    for t in transactions:

        debit = ""
        credit = ""

        if t.transaction_type == "DEPOSIT":
            running_balance += t.amount
            credit = t.amount
        else:
            running_balance -= t.amount
            debit = t.amount

        p.setFillColor(colors.whitesmoke)
        p.rect(40, y, width - 80, 20, fill=1)

        p.setFillColor(colors.black)
        p.setFont("Helvetica", 9)

        # Date & Time (IST)
        txn_time = timezone.localtime(t.timestamp)

        p.drawString(50, y + 5, txn_time.strftime("%d-%m-%Y"))
        p.drawString(110, y + 5, txn_time.strftime("%I:%M %p"))

        p.drawString(180, y + 5, t.transaction_type)

        # Debit
        p.setFillColor(colors.red)
        p.drawString(270, y + 5, f"{debit:.2f}" if debit else "")

        # Credit
        p.setFillColor(colors.green)
        p.drawString(360, y + 5, f"{credit:.2f}" if credit else "")

        # Balance
        p.setFillColor(colors.black)
        p.drawString(450, y + 5, f"{running_balance:.2f}")

        y -= 22

        # PAGE BREAK
        if y < 80:
            p.showPage()
            y = height - 100

    # ================= FOOTER =================
    p.setFillColor(colors.grey)
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(width / 2, 30,
        "This is a system generated statement and does not require signature.")

    p.save()
    return response

from django.contrib.auth.models import User
from django.contrib import messages
import random

def forgot_password(request):
    if request.method == "POST":
        username = request.POST.get('username')

        try:
            user = User.objects.get(username=username)

            otp = random.randint(100000, 999999)

            OTP.objects.create(user=user, otp=otp)

            request.session['reset_user_id'] = user.id

            print("RESET OTP:", otp)

            return redirect('verify_reset_otp')

        except User.DoesNotExist:
            messages.error(request, "Username not found")

    return render(request, 'forgot_password.html')

def verify_reset_otp(request):
    user_id = request.session.get('reset_user_id')

    if not user_id:
        return redirect('forgot_password')

    from django.contrib.auth.models import User
    user = User.objects.get(id=user_id)

    otp_obj = OTP.objects.filter(user=user).order_by('-created_at').first()

    if request.method == "POST":
        entered_otp = request.POST.get('otp')

        if str(entered_otp) == str(otp_obj.otp):
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid OTP")

    return render(request, 'verify_reset_otp.html', {
        'otp': otp_obj.otp
    })

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User

def reset_password(request):
    user_id = request.session.get('reset_user_id')

    if not user_id:
        return redirect('forgot_password')

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if pass1 != pass2:
            messages.error(request, "Passwords do not match")
            return redirect('reset_password')

        # ✅ SUCCESS CASE
        user.set_password(pass1)
        user.save()

        request.session.pop('reset_user_id', None)

        messages.success(request, "Password reset successful! Redirecting to login...")

        # 👇 send success flag ONLY ONCE
        return render(request, 'reset_password.html', {
            'success': True
        })

    # ✅ NORMAL PAGE LOAD (NO redirect flag)
    return render(request, 'reset_password.html')