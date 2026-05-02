import stripe
from datetime import timedelta, date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from .models import Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY


# ---------------------------------------------------------
# Auth
# ---------------------------------------------------------

def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')

        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return render(request, 'accounts/signup.html')

        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/signup.html')

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'accounts/signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'accounts/signup.html')

        user = User.objects.create_user(username=email, email=email, password=password)
        login(request, user)
        messages.success(request, 'Account created. Please choose a plan to continue.')
        return redirect('choose_plan')

    return render(request, 'accounts/signup.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('home')
    return redirect('home')


def logout_view(request):
    logout(request)
    return redirect('home')


# ---------------------------------------------------------
# Plans & Stripe
# ---------------------------------------------------------

@login_required
def choose_plan(request):
    try:
        if request.user.subscription.is_valid:
            return redirect('home')
    except Subscription.DoesNotExist:
        pass
    return render(request, 'accounts/choose_plan.html')


@login_required
def create_checkout_session(request):
    if request.method != 'POST':
        return redirect('choose_plan')

    plan = request.POST.get('plan')

    if plan == '3_month':
        price_id = settings.STRIPE_PRICE_3_MONTH
    elif plan == '6_month':
        price_id = settings.STRIPE_PRICE_6_MONTH
    else:
        messages.error(request, 'Invalid plan selected.')
        return redirect('choose_plan')

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            customer_email=request.user.email,
            metadata={'plan': plan, 'user_id': str(request.user.id)},
            success_url=request.build_absolute_uri('/accounts/payment/success/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/accounts/payment/cancel/'),
        )
        return redirect(session.url)
    except Exception as e:
        messages.error(request, 'Something went wrong. Please try again.')
        return redirect('choose_plan')


@login_required
def payment_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('choose_plan')

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        plan = session.metadata.get('plan', '3_month')
        duration_days = 90 if plan == '3_month' else 180

        Subscription.objects.update_or_create(
            user=request.user,
            defaults={
                'plan': plan,
                'stripe_customer_id': session.get('customer', ''),
                'stripe_subscription_id': session.get('subscription', ''),
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=duration_days),
                'is_active': True,
            },
        )
    except Exception:
        messages.error(request, 'There was an issue confirming your payment. Please contact support.')
        return redirect('choose_plan')

    return render(request, 'accounts/payment_success.html')


@login_required
def payment_cancel(request):
    messages.warning(request, 'Payment cancelled. You can choose a plan anytime.')
    return redirect('choose_plan')


# ---------------------------------------------------------
# Stripe Webhook
# ---------------------------------------------------------

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return HttpResponse(status=400)

    data = event['data']['object']

    if event['type'] == 'customer.subscription.deleted':
        Subscription.objects.filter(
            stripe_subscription_id=data['id']
        ).update(is_active=False)

    elif event['type'] == 'invoice.payment_succeeded':
        sub_id = data.get('subscription')
        if sub_id:
            Subscription.objects.filter(
                stripe_subscription_id=sub_id
            ).update(is_active=True)

    elif event['type'] == 'invoice.payment_failed':
        sub_id = data.get('subscription')
        if sub_id:
            Subscription.objects.filter(
                stripe_subscription_id=sub_id
            ).update(is_active=False)

    elif event['type'] == 'customer.subscription.updated':
        Subscription.objects.filter(
            stripe_subscription_id=data['id']
        ).update(is_active=data['status'] == 'active')

    return HttpResponse(status=200)