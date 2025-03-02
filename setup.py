from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read README for long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="instagram-downloader",
    version="0.1.0",
    author="Mohammad Rasol Esfandiari",
    author_email="mrasolesfandiari@gmail.com",
    description="A Python library for downloading Instagram content with manual login functionality",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/esfiam/instagram-downloader",
    packages=find_packages(),
    py_modules=["manage_sessions"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "instagram-sessions=manage_sessions:main",
        ],
    },
) 