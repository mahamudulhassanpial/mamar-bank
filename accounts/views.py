from django.shortcuts import render, redirect
from django.views.generic import FormView
from .forms import UserRegistrationForm, UserUpdateForm, UserPasswordChangeForm
from django.contrib.auth import login, logout
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.views import View
from django.contrib import messages
import datetime
from transactions.views import send_mail_to_user

class UserPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("profile")

    def form_valid(self, form):
        current_datetime = datetime.datetime.now()

        messages.success(self.request, f"""Your password has been changed""")

        send_mail_to_user("You password has been changed", 'accounts/password_change_mail.html', {
            'time': current_datetime.strftime("%A, %B %d, %Y")
        }, self.request.user.email)

        return super().form_valid(form)

class UserRegistrationView(FormView):
    # template_name = 'accounts/user_registration.html'
    # form_class = UserRegistrationForm
    # success_url = reverse_lazy('profile')
    
    # def form_valid(self,form):
    #     print(form.cleaned_data)
    #     user = form.save()
    #     login(self.request, user)
    #     print(user)
    #     return super().form_valid(form) # form_valid function call hobe jodi sob thik thake

    template_name = 'accounts/user_registration_form.html'
    success_url = reverse_lazy("register")
    form_class = UserRegistrationForm

    def form_valid(self, form):
        user = form.save()
        login(self.request, user=user)
        return super().form_valid(form)

class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    def get_success_url(self):
        return reverse_lazy('home')

class UserLogoutView(LogoutView):
    def get_success_url(self):
        if self.request.user.is_authenticated:
            logout(self.request)
        return reverse_lazy('home')


class UserBankAccountUpdateView(View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        form = UserUpdateForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the user's profile page
        return render(request, self.template_name, {'form': form})
    
    
    