from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import stripe
from datetime import timedelta, date
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import Subscription
from django.contrib.auth.hashers import make_password

# ---------------------------------------------------------
# STRIPE CONFIG
# ---------------------------------------------------------
stripe.api_key = settings.STRIPE_SECRET_KEY


def logout_view(request):
    logout(request)
    return redirect("home")





def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You have been logged out successfully.")
            return redirect("home")  # redirects to homepage after login
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("home")  # stays on homepage with error message
    else:
        return redirect("home")
    

  

# ---------------------------------------------------------
# SIGNUP VIEW → redirect user to choose plan
# ---------------------------------------------------------

def signup_view(request):
    if request.method == "POST":
        email = request.POST.get("email").strip().lower()
        password = request.POST.get("password")

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists. Please log in instead.")
            return redirect("login")

        # Create user
        user = User.objects.create_user(username=email, email=email, password=password)
        user.save()

        # ✅ Log the user in immediately
        login(request, user)

        messages.success(request, "Your account has been created successfully. Please choose your plan.")
        return redirect("choose_plan")

    return render(request, "accounts/signup.html")


# ---------------------------------------------------------
# CHOOSE PLAN PAGE
# ---------------------------------------------------------
@login_required
def choose_plan(request):
    return render(request, "accounts/choose_plan.html")


# ---------------------------------------------------------
# STRIPE CHECKOUT SESSION CREATION
# ---------------------------------------------------------
@login_required
@csrf_exempt
def create_checkout_session(request):
    if request.method == "POST":
        plan = request.POST.get("plan")

        if plan == "3_month":
            price_id = "price_1SM3ELKPRXR2L86txpqmJzQh"
        elif plan == "6_month":
            price_id = "price_1SM3EzKPRXR2L86ty1Nr9jcb"
        else:
            return JsonResponse({"error": "Invalid plan"}, status=400)

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    },
                ],
                mode="subscription",
                customer_email=request.user.email,
                success_url=f"http://localhost:8000/accounts/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url="http://localhost:8000/accounts/payment-cancel/",
            )
            return redirect(checkout_session.url)
        except Exception as e:
            return JsonResponse({"error": str(e)})

    return JsonResponse({"error": "Invalid request"}, status=400)



def password_reset_view(request):
    if request.method == "POST":
        # Safely get email even if it's missing
        email = (request.POST.get("email") or "").strip().lower()

        # If we're on the "enter email" step
        if "new_password" not in request.POST:
            if not email:
                messages.error(request, "Please enter your email.")
                return render(request, "accounts/password_reset.html")

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "No account found with this email. Please sign up first.")
                return render(request, "accounts/password_reset.html")

            # ✅ Show reset form
            return render(request, "accounts/password_reset.html", {"email": email, "allow_reset": True})

        # If we're on the "reset password" step
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not email:
            messages.error(request, "Something went wrong. Please start over.")
            return redirect("password_reset")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with this email. Please sign up first.")
            return render(request, "accounts/password_reset.html")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/password_reset.html", {"email": email, "allow_reset": True})

        user.password = make_password(new_password)
        user.save()
        messages.success(request, "Your password has been reset successfully. You can now log in.")
        return redirect("login")

    # GET request — show the basic email form
    return render(request, "accounts/password_reset.html")


# ---------------------------------------------------------
# PAYMENT SUCCESS VIEW
# ---------------------------------------------------------
@login_required
def payment_success(request):
    session_id = request.GET.get("session_id")
    if not session_id:
        return redirect("choose_plan")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        # Determine plan duration by price ID (or set metadata on session for cleaner logic)
        plan_name = "3_month"
        if session.get("line_items"):
            item = session["line_items"]["data"][0]
            if "6" in item["description"]:
                plan_name = "6_month"

        # Set end date based on plan
        duration_days = 90 if plan_name == "3_month" else 180

        Subscription.objects.update_or_create(
            user=request.user,
            defaults={
                "plan": plan_name,
                "stripe_customer_id": customer_id,
                "stripe_subscription_id": subscription_id,
                "start_date": date.today(),
                "end_date": date.today() + timedelta(days=duration_days),
                "is_active": True,
            },
        )

    except Exception as e:
        print("Stripe error:", e)
        messages.error(request, "There was an issue confirming your payment.")
        return redirect("choose_plan")

    return render(request, "accounts/payment_success.html")


# ---------------------------------------------------------
# PAYMENT CANCEL VIEW
# ---------------------------------------------------------
@login_required
def payment_cancel(request):
    messages.warning(request, "Payment canceled. You can choose a plan again anytime.")
    return redirect("choose_plan")


# ---------------------------------------------------------
# STRIPE WEBHOOK (auto-manages cancellations, renewals)
# ---------------------------------------------------------
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print("⚠️ Webhook error:", e)
        return HttpResponse(status=400)

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "customer.subscription.deleted":
        sub_id = data["id"]
        Subscription.objects.filter(stripe_subscription_id=sub_id).update(is_active=False)

    elif event_type == "invoice.payment_succeeded":
        sub_id = data.get("subscription")
        if sub_id:
            Subscription.objects.filter(stripe_subscription_id=sub_id).update(is_active=True)

    elif event_type == "customer.subscription.created":
        sub_id = data["id"]
        customer_id = data["customer"]
        Subscription.objects.filter(stripe_customer_id=customer_id).update(
            stripe_subscription_id=sub_id, is_active=True
        )

    return HttpResponse(status=200)


