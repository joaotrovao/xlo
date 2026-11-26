from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('criar-conta/', views.criar_conta, name='criarconta'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('home/<str:cat>/', views.home_cat, name='category_items'),
    path('home/<str:cat>/<str:sub>/', views.home_sub, name='category_sub_items'),
    path('item/<int:ref>/', views.view_item, name='view_item'),
    path('perfil/<int:utilizador_username_id>', views.view_perfil, name='view_perfil'),
    path('perfil/newitem/<int:utilizador_username_id>', views.add_item_view, name='add_item_view'),
    path('item/<int:ref>/compra/', views.compra, name='compra'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
