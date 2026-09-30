"""URL configuration for JOCKY Command Console."""

from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("api/auth/login/",                             views.api_login,            name="api_login"),

    # Health
    path("api/health/",                                 views.api_health,            name="api_health"),

    # Case
    path("api/auth/cases/<str:case_id>/",               views.api_case,              name="api_case"),

    # Compiler
    path("api/compiler/compile/",                       views.api_compile,           name="api_compile"),

    # Forge
    path("api/forge/builds/<str:case_id>/",             views.api_forge_builds,      name="api_forge_builds"),
    path("api/forge/deploy/",                           views.api_dispatch,          name="api_dispatch"),

    # Endpoints
    path("api/endpoints/",                              views.api_endpoints,         name="api_endpoints"),

    # Graph + Timeline
    path("api/graph/<str:case_id>/HOST-01/",            views.api_graph,             name="api_graph"),
    path("api/timeline/<str:case_id>/HOST-01/",         views.api_timeline,          name="api_timeline"),

    # Findings
    path("api/findings/<str:case_id>/",                 views.api_correlate,         name="api_correlate"),

    # AI
    path("api/ai/explain/<str:finding_id>/",            views.api_ai_explain,        name="api_ai_explain"),

    # Kernel
    path("api/kernel/<str:case_id>/<str:host>/",        views.api_kernel,            name="api_kernel"),

    # Blockchain
    path("api/blockchain/verify/",                      views.api_blockchain_verify, name="api_blockchain_verify"),
    path("api/blockchain/tamper-demo/",                 views.api_blockchain_tamper, name="api_blockchain_tamper"),
    path("api/blockchain/verify/<str:evidence_id>/",    views.api_integrity,         name="api_integrity"),

    # Reports
    path("api/reports/<str:case_id>/pdf/",              views.api_report_pdf,        name="api_report_pdf"),
    path("api/reports/<str:case_id>/json/",             views.api_report_json,       name="api_report_json"),
    path("api/reports/generate/<str:case_id>/",         views.api_report_generate,   name="api_report_generate"),
    path("api/reports/<str:case_id>/",                  views.api_report_stats,      name="api_report_stats"),

    # Query
    path("api/query/",                                  views.api_query,             name="api_query"),

    # Catch-all for SPA
    path("",                                            views.console_home,          name="console_home"),
]
