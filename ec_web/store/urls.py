from django.urls import path
from . import views

urlpatterns = [
    path('',views.store,name='homepage'),
    path('index/',views.Index.as_view(),name='index'),
    path('cart/',views.Cart.as_view(),name='cart'),
    path('update-cart/', views.Index.as_view(), name='update_cart'),
    path('checkout/',views.CheckOut.as_view(),name='checkout'),
    path('payment/',views.PaymentView.as_view(), name='payment'),
    path('orders/',views.OrderView.as_view(),name='orders'),
    path('payment/', views.PaymentView.as_view(), name='payment'),
    path('login/',views.Login.as_view(),name='login'),
    path('signup/',views.Signup.as_view(),name='signup'),
    path('payment/confirm/', views.PaymentConfirm.as_view(), name='payment_confirm'),
    path('complete-profile/', views.CompleteProfile.as_view(),name='complete_profile'),
    path('logout/',views.logout,name='logout'),
]