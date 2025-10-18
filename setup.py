"""
ATS MAFIA Framework Setup Configuration
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "ATS MAFIA Framework - Advanced Training System for Multi-Agent Interactive Framework"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return [
        'asyncio',
        'logging',
        'json',
        'yaml',
        'pydantic',
        'typing-extensions',
        'dataclasses',
        'pathlib',
        'datetime',
        'threading',
        'queue',
        'socket',
        'http.client',
        'urllib.parse',
        'hashlib',
        'base64',
        'uuid',
        're',
        'copy',
        'itertools',
        'collections',
        'functools',
        'inspect',
        'importlib',
        'sys',
        'os',
        'time',
        'random',
        'string',
        'math',
        'statistics'
    ]

setup(
    name="ats-mafia-framework",
    version="1.0.0",
    author="ATS MAFIA Team",
    author_email="team@atsmafia.com",
    description="Advanced Training System for Multi-Agent Interactive Framework",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/atsmafia/framework",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
        "Topic :: Education",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18",
            "pytest-cov>=2.12",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.910",
            "pre-commit>=2.15"
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
            "myst-parser>=0.15"
        ],
        "voice": [
            "speechrecognition>=3.8",
            "pyttsx3>=2.90",
            "pyaudio>=0.2.11"
        ],
        "ui": [
            "streamlit>=1.0",
            "plotly>=5.0",
            "pandas>=1.3"
        ]
    },
    entry_points={
        "console_scripts": [
            "ats-mafia=ats_mafia_framework.cli.main:cli_main",
            "ats-orchestrator=ats_mafia_framework.cli.orchestrator:main",
            "ats-profile=ats_mafia_framework.cli.profile:main"
        ]
    },
    include_package_data=True,
    package_data={
        "ats_mafia_framework": [
            "config/*.yaml",
            "config/*.json",
            "profiles/*.json",
            "scenarios/*.json",
            "tools/*.py",
            "docs/*.md"
        ]
    },
    zip_safe=False,
    keywords="artificial intelligence, multi-agent, training, security, simulation, framework"
)