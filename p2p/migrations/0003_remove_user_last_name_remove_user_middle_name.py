# Generated by Django 5.0 on 2024-05-28 16:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('p2p', '0002_remove_user_is_cashier_alter_transaction_listing'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='user',
            name='middle_name',
        ),
    ]
