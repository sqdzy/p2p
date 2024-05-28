import pytz
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.hashers import check_password, make_password
from .models import *
from .cbrf_parser import Rates
import datetime
from decimal import Decimal

def index(request):
    rates = Rates()
    rates.get_rates()
    currency_rates = get_currency_rates()
    preferred_currency = request.user.currencypreference_set.first().currency.currency_code if request.user.is_authenticated and request.user.currencypreference_set.exists() else "USD"
    context = {
        "currency_rates": currency_rates,
        "preferred_currency": preferred_currency,
        "preferred_currency_rate": currency_rates.get(preferred_currency),
    }
    return render(request, "index.html", context)

from django.contrib.auth import authenticate, login

def get_currency_rates():
    rates = ExchangeRate.objects.all()
    return {rate.currency_code.currency_code: round(rate.rate, 2) for rate in rates}

def auth(request):
    currency_rates = get_currency_rates()
    preferred_currency = request.user.currencypreference_set.first().currency.currency_code if request.user.is_authenticated and request.user.currencypreference_set.exists() else "USD"
    context = {
        "currency_rates": currency_rates,
        "preferred_currency": preferred_currency,
        "preferred_currency_rate": currency_rates.get(preferred_currency),
    }
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session["username"] = username
            return redirect("index")
        else:
            return render(request, "auth.html", {"error": "Неверное имя пользователя или пароль", **context})
    return render(request, "auth.html", context=context)



def register(request):
    currency_rates = get_currency_rates()
    preferred_currency = request.user.currencypreference_set.first().currency.currency_code if request.user.is_authenticated and request.user.currencypreference_set.exists() else "USD"
    context = {
        'currency_rates': currency_rates,
        'preferred_currency': preferred_currency,
        "preferred_currency_rate": currency_rates.get(preferred_currency),
    }
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        if password != confirm_password:
            return render(request, "register.html", {"error": "Пароли не совпадают"})
        hashed_password = make_password(password)
        user = User.objects.create(username=username, email=email, password=hashed_password)
        login(request, user)
        request.session["username"] = username
        return redirect("index")
    return render(request, "register.html", context=context)


@login_required
def user_profile(request, username):
    user = get_object_or_404(User, username=username)

    if request.user != user:
        return HttpResponseForbidden("Вам недоступен просмотр этого профиля")

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", user.first_name)
        user.save()
        return redirect("user_profile", username=user.username)

    transactions = user.transactions.all()
    listings = user.listings.filter(amount__gt=0) if user.is_seller else None

    currency_rates = get_currency_rates()
    preferred_currency = request.user.currencypreference_set.first().currency.currency_code if request.user.is_authenticated and request.user.currencypreference_set.exists() else "USD"

    context = {
        'user': user,
        'transactions': transactions,
        'listings': listings,
        'currency_rates': currency_rates,
        'preferred_currency': preferred_currency,
        'show_name_form': not bool(user.first_name),
        "preferred_currency_rate": currency_rates.get(preferred_currency),
    }

    return render(request, 'user.html', context=context)

def listings(request):
    listings = Listing.objects.all().filter(amount__gt=0)
    currency_rates = get_currency_rates()
    preferred_currency = request.user.currencypreference_set.first().currency.currency_code if request.user.is_authenticated and request.user.currencypreference_set.exists() else "USD"
    context = {
        "listings": listings,
        "currency_rates": currency_rates,
        "preferred_currency": preferred_currency,
        "preferred_currency_rate": currency_rates.get(preferred_currency),
    }
    return render(request, "listing.html", context)

@login_required
def create_listing(request):
    if not request.user.is_seller:
        return redirect('listings')

    if request.method == 'POST':
        currency_code = request.POST.get('currency_code')
        is_buy = request.POST.get('is_buy') == 'buy'
        amount = request.POST.get('amount')
        price = request.POST.get('price')
        payment_method_id = request.POST.get('payment_method')

        currency = Currency.objects.get(currency_code=currency_code)
        payment_method = PaymentMethod.objects.get(payment_method_id=payment_method_id)

        Listing.objects.create(
            user_id=request.user,
            currency_code=currency,
            is_buy=is_buy,
            amount=amount,
            price=price,
            payment_method=payment_method,
            created_at = datetime.datetime.now(pytz.timezone("Europe/Moscow")
        ))
        return redirect('listings')
    currency_rates = get_currency_rates()
    preferred_currency = request.user.currencypreference_set.first().currency.currency_code if request.user.is_authenticated and request.user.currencypreference_set.exists() else "USD"
    currencies = Currency.objects.all()
    exchangerate = ExchangeRate.objects.all()
    currencies_rates = [{"currency_code": currency.currency_code,
                         "currency_name": currency.currency_name,
                        "currency_rate": round(exchangerate.get(currency_code_id=currency.currency_code).rate, 2)} for currency in currencies]
    payment_methods = PaymentMethod.objects.all()

    context = {
        'currencies': currencies_rates,
        'payment_methods': payment_methods,
        "currency_rates": currency_rates,
        "preferred_currency": preferred_currency,
        "preferred_currency_rate": currency_rates.get(preferred_currency),

    }
    return render(request, 'create_listing.html', context)


@login_required
def purchase_currency(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if listing.user_id == request.user:
        return render(request, 'purchase_currency.html', {'listing': listing, 'error': 'Вы не можете купить валюту у себя'})

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))

        if amount > listing.amount:
            return render(request, 'purchase_currency.html', {'listing': listing, 'error': 'Недостаточно валюты для покупки'})

        total_price = amount * Decimal(listing.price)

        if request.user.balance < total_price:
            return render(request, 'purchase_currency.html', {'listing': listing, 'error': 'Недостаточно средств'})

        request.user.balance -= total_price
        listing.user_id.balance += total_price
        request.user.save()
        listing.user_id.save()

        Transaction.objects.create(
            user=request.user,
            listing=listing,
            amount=amount,
            total_price=total_price,
            is_buy=True
        )

        listing.amount -= amount
        listing.save()

        CurrencyPreference.objects.update_or_create(user=request.user, defaults={'currency': listing.currency_code})

        return redirect('listings')

    return render(request, 'purchase_currency.html', {'listing': listing})



@login_required
def sell_currency(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if listing.user_id == request.user:
        return render(request, 'sell_currency.html', {'listing': listing, 'error': 'Вы не можете продать валюту себе'})

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))

        if amount > listing.amount:
            return render(request, 'sell_currency.html', {'listing': listing, 'error': 'Пользователю не нужно столько валюты'})

        total_price = amount * Decimal(listing.price)

        if request.user.balance < total_price:
            return render(request, 'sell_currency.html', {'listing': listing, 'error': 'Недостаточно валюты для продажи'})

        request.user.balance += total_price
        listing.user_id.balance -= total_price
        request.user.save()
        listing.user_id.save()

        Transaction.objects.create(
            user=request.user,
            listing=listing,
            amount=amount,
            total_price=total_price,
            is_buy=False
        )

        listing.amount -= amount
        listing.save()

        CurrencyPreference.objects.update_or_create(user=request.user, defaults={'currency': listing.currency_code})

        return redirect('listings')

    return render(request, 'sell_currency.html', {'listing': listing})

@login_required
def delete_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if listing.user_id != request.user:
        return HttpResponseForbidden("У вас нет прав на удаление этого объявления")

    listing.delete()
    return redirect('user_profile', username=request.user.username)

def logout_view(request):
    logout(request)
    return redirect("index")
