from django.urls import path
from . import views
from django.contrib.auth.views import LoginView
from .views import SignUpView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path("",views.home, name='home'),#カレントディレクトリにアクセスしたときviews.homeを呼び出す
    path('abst',views.abst, name='abst'), 
    path('your_view_function',views.your_view_function, name='your_view_function'), 
    path('sort',views.some_view, name='sort'), 
    path('test',views.home, name='test'),   
    path('export',views.csv_export, name='csv_export'),
    path('import', views.import_impact_factors, name='import_impact_factors'),

]