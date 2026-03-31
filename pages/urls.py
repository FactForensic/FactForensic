from django.urls import path
from .views import home_view, analyze_view
from pages.views import trigger_fetch

urlpatterns = [
    path("", home_view, name="home"),
    path("analyze/", analyze_view, name="analyze"),
    path("api/trigger-fetch/", trigger_fetch, name="trigger_fetch"),
]
