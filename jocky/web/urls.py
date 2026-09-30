"""URL configuration for JOCKY Command Console."""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.console_home, name="console_home"),
    path("api/health/", views.api_health, name="api_health"),
    path("api/auth/cases/<str:case_id>/", views.api_case, name="api_case"),
    path("api/compiler/compile/", views.api_compile, name="api_compile"),
    path("api/forge/deploy/", views.api_dispatch, name="api_dispatch"),
    path("api/findings/<str:case_id>/", views.api_correlate, name="api_correlate"),
    path("api/blockchain/verify/<str:evidence_id>/", views.api_integrity, name="api_integrity"),
    path("api/graph/<str:case_id>/HOST-01/", views.api_graph, name="api_graph"),
    path("api/timeline/<str:case_id>/HOST-01/", views.api_timeline, name="api_timeline"),
    path("api/query/", views.api_query, name="api_query"),
]
