
from django.urls import path
from .views import UserRegistrationView, UserLoginView, UserLogoutView,UserBankAccountUpdateView, UserPasswordChangeView
 
urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('change_password/', UserPasswordChangeView.as_view(),name="change_password"),
    path('profile/', UserBankAccountUpdateView.as_view(), name='profile' )
]