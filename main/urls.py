from django.urls import include, path
from knox import views as knox_views

from main import views, auth_views

urlpatterns = [
    path('whiteflag/authenticate/', views.whiteflag_authenticate),
    path(
        'whiteflag/discontinue_authentication/',
        views.whiteflag_discontinue_authentication,
    ),
    path('whiteflag/encode/', views.whiteflag_encode),
    path('whiteflag/decode/', views.whiteflag_decode),
    path('create_account/', views.create_account),
    path('get_account_balance/', views.get_account_balance),
    path('get_fee_for_new_signal/', views.get_fee_for_new_signal),
    path('send_new_signal/', views.send_new_signal),
    path('get_signal_history/', views.get_signal_history),
    path('auth/register/', auth_views.UserRegisterView.as_view()),
    path('auth/login/', auth_views.LoginAPIView.as_view()),
    path('auth/user/', auth_views.UserAPI.as_view()),
    path('auth/logout/', knox_views.LogoutView.as_view(), name='knox_logout')
]
