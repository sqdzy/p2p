"""
URL configuration for p2p_for_db project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from p2p import views
from django.urls import path
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls, name = "admin"),
    path('', views.index, name = "index"),
    path('auth/', views.auth, name='auth'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('listing/', views.listings, name = 'listings'),
    path('create_listing/', views.create_listing, name='create_listing'),
    path('purchase_currency/<int:listing_id>', views.purchase_currency, name = 'purchase_currency'),
    path('sell_currency/<int:listing_id>', views.sell_currency, name='sell_currency'),
    path('listing/<int:listing_id>/delete/', views.delete_listing, name='delete_listing'),
]
