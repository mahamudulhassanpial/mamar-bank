# Generated by Django 5.1.2 on 2025-01-29 18:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_userbankaccount_account_type_and_more'),
        ('transactions', '0003_alter_transaction_transaction_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transactions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('balance_after_transaction', models.DecimalField(decimal_places=2, max_digits=12)),
                ('transaction_type', models.IntegerField(choices=[(1, 'Deposit'), (2, 'Withdrawal'), (3, 'Loan'), (4, 'Loan paid'), (5, 'Send money'), (6, 'Receive money')])),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('loan_approval', models.BooleanField(default=False)),
                ('is_bank_bankrupt', models.BooleanField(blank=True, default=False, null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='accounts.userbankaccount')),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
        migrations.DeleteModel(
            name='Transaction',
        ),
    ]
