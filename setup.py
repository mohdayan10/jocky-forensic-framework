"""JOCKY — Forensic Investigation Framework"""

from setuptools import setup, find_packages

setup(
    name="jocky",
    version="0.1.0",
    description="JOCKY — From Program to Verified Investigation",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "django>=4.2",
        "anthropic>=0.39.0",
        "cryptography>=41.0",
    ],
    entry_points={
        "console_scripts": [
            "jocky=jocky.cli:main",
        ],
    },
    package_data={
        "jocky": ["web/templates/*.html"],
    },
)
