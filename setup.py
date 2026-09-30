"""JOCKY — Forensic Investigation Framework"""

from setuptools import setup, find_packages

setup(
    name="jocky",
    version="2.0.0",
    description="JOCKY — From Program to Verified Investigation",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        # Compiler
        "lark>=1.1.7",
        "cryptography>=41.0.0",

        # Forge (optional — falls back to simulation if unavailable)
        "pycryptodome>=3.19.0",

        # Backend
        "django>=4.2.0",
        "djangorestframework>=3.14.0",
        "channels>=4.0.0",
        "daphne>=4.0.0",

        # AI
        "anthropic>=0.39.0",
        "groq>=0.9.0",

        # Reports
        "python-dateutil>=2.8.0",

        # Web
        "django-cors-headers>=4.3.0",

        # Utilities
        "pyjwt>=2.8.0",
    ],
    extras_require={
        "full": [
            "llvmlite>=0.41.0",
            "pefile>=2023.2.7",
            "pyelftools>=0.29",
            "channels-redis>=4.1.0",
            "celery>=5.3.0",
            "redis>=5.0.0",
            "psycopg2-binary>=2.9.0",
            "reportlab>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "jocky=jocky.cli:main",
        ],
    },
    package_data={
        "jocky": [
            "web/templates/*.html",
            "byovd_db.json",
            "frontend/src/**/*",
        ],
    },
)
