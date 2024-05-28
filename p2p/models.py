from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(
            username=username,
            email=email,
            password=password,
        )
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=50)
    is_seller = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

class Currency(models.Model):
    currency_code = models.CharField(max_length=3, primary_key=True, unique=True)
    currency_name = models.CharField(max_length=50)

class ExchangeRate(models.Model):
    exchange_rate_id = models.AutoField(primary_key=True)
    currency_code = models.OneToOneField(Currency, on_delete=models.CASCADE)
    effective_date = models.DateField()
    rate = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        unique_together = ('currency_code', 'effective_date',)

class Listing(models.Model):
    listing_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    currency_code = models.ForeignKey(Currency, on_delete=models.CASCADE)
    is_buy = models.BooleanField()
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    price = models.DecimalField(max_digits=10, decimal_places=4)
    payment_method = models.ForeignKey('PaymentMethod', on_delete=models.CASCADE)
    created_at = models.DateTimeField()

class PaymentMethod(models.Model):
    payment_method_id = models.AutoField(primary_key=True)
    payment_method_name = models.CharField(max_length=50)
    payment_method_description = models.CharField(max_length=200, blank=True, null=True)

class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True)  # Изменено на SET_NULL
    transaction_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    total_price = models.DecimalField(max_digits=18, decimal_places=4)
    is_buy = models.BooleanField()

class CurrencyPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'currency')
