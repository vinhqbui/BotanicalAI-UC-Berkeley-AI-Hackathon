from django.urls import path

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from . import views

urlpatterns = [
    path('organizations/', views.OrganizationListView.as_view(), name='org.list'),
    path('organizations/<int:pk>', views.OrganizationDetailView.as_view(), name='org.detail'),
    path('chat/', views.llama_chat, name='chat'),
    path('upload/', views.upload, name='upload'),
    path('page/', views.page, name='page')
]

urlpatterns += staticfiles_urlpatterns()