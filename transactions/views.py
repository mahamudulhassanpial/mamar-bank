from typing import Any
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Sum
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from core.models import Bank
from .models import Transactions
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from accounts.models import UserBankAccount
from .constants import DEPOSIT, LOAN, LOAN_PAID, WITHDRAWAL, SEND_MONEY, RECEIVE_MONEY
from .forms import DepositForm, WithdrawalForm, LoanRequestForm, SendMoneyForm
# Create your views here.

def send_transaction_email(user, amount, subject, template):
    message = render_to_string(template, {
        'user' : user,
        'amount': amount,
    })
    send_email = EmailMultiAlternatives(subject, '', to=[user.email])
    send_email.attach_alternative(message, "text/html")
    send_email.send()

class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transactions
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # template e context data pass kora
        context.update({
            'title': self.title
        })

        return context

class SendMoneyView(TransactionCreateMixin):
    title = "Send money"
    form_class = SendMoneyForm
    template_name = 'transactions/send_money.html'

    def get_initial(self):
        initial = {
            'transaction_type': SEND_MONEY
        }
        print("Initial data:", initial)
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data['amount']
        account_no = form.cleaned_data['account_no']

        receiver_account = UserBankAccount.objects.get(account_no=account_no)
        receiver_account.balance += amount
        receiver_account.save(update_fields=['balance'])

        receiver_transaction = Transactions(amount=amount, transaction_type=RECEIVE_MONEY, account=receiver_account, balance_after_transaction=receiver_account.balance)
        receiver_transaction.save()

        sender_account = self.request.user.account
        sender_account.balance -= amount
        sender_account.save(update_fields=['balance'])

        messages.success(self.request, f"""{amount} has been sent to Account:  {account_no}""")
        return super().form_valid(form)


class DepositMoneyView(TransactionCreateMixin):
    success_url = reverse_lazy("transaction_report")
    title = 'Deposit Money'

    form_class = DepositForm

    def get_initial(self):
        initial = {
            'transaction_type': DEPOSIT
        }
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account

        account.balance += amount
        account.save(update_fields=['balance'])
        messages.success(self.request, f"""{amount} is deposited to your account """)
        # mail_subject = "Deposite Message"
        # message = render_to_string('transactions/deposite_email.html', {
        #     'user' : self.request.user,
        #     'amount': amount,
        # })
        # to_email = self.request.user.email
        # send_email = EmailMultiAlternatives(mail_subject, '', to=[to_email])
        # send_email.attach_alternative(message, "text/html")
        # send_email.send()
        send_transaction_email(self.request.user, amount, "Deposite Message", "transactions/deposite_email.html")
        return super().form_valid(form)


class WithdrawalMoneyView(TransactionCreateMixin):
    success_url = reverse_lazy("transaction_report")
    title = 'Withdraw Money'

    form_class = WithdrawalForm

    def get_initial(self):
        initial = {
            'transaction_type': WITHDRAWAL
        }
        return initial

    def form_valid(self, form):
        bank = Bank.objects.get(name='mamar_bank')
        # if not bank.status: if bank is bankrupt 
        if bank.status:
            amount = form.cleaned_data.get('amount')
            account = self.request.user.account

            account.balance -= amount
            account.save(update_fields=['balance'])

            messages.success(self.request, f"""{amount} is withdrawn from your account """)
            send_transaction_email(self.request.user, amount, "Withdrawl Message", "transactions/withdrawl_email.html")
            return super().form_valid(form)
        else:
            messages.error(
                self.request, f"""Can't withdraw money bank is bankrupt""")
            
            return redirect("home")


class LoanMoneyView(TransactionCreateMixin):
    title = 'Request For Loan'

    form_class = LoanRequestForm

    def get_initial(self):
        initial = {
            'transaction_type': LOAN
        }
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')

        current_loan_count = Transactions.objects.filter(account=self.request.user.account, loan_approval=True, transaction_type=LOAN).count()

        if current_loan_count >= 3:
            return HttpResponse("Loan limit exceeded")

        messages.success(self.request, f"""Loan request for {amount} successfully sent""")
        send_transaction_email(self.request.user, amount, "Loan Request Message", "transactions/loan_email.html")
        return super().form_valid(form)


class TransactionReportView(LoginRequiredMixin, ListView):
    model = Transactions
    template_name = 'transactions/transaction_report.html'
    balance = 0

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )

        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            queryset = queryset.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date)

            self.balance = Transactions.objects.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account"] = self.request.user.account
        return context


class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transactions, id=loan_id)

        if loan.loan_approval:
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('transaction_report')
            else:
                return redirect('transaction_report')


class LoanListView(LoginRequiredMixin, ListView):
    model = Transactions
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transactions.objects.filter(account=user_account, transaction_type=LOAN)
        return queryset