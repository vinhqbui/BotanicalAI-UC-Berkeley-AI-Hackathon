from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('authorized/', views.AuthorizedView.as_view(), name='authorized'),
]

#urlpatterns += staticfiles_urlpatterns()