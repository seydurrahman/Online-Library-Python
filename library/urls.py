from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect

app_name = 'library'
def logout_view(request):
    logout(request)
    return redirect('library:index')

urlpatterns = [
    path('', views.index, name='index'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),
    path('add-book/', views.add_book, name='add_book'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(
    template_name='library/login.html',
    redirect_authenticated_user=True,
    next_page='library:index'
), name='login'),
    path('logout/', logout_view, name='logout'),
]
