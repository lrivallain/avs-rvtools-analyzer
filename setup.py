from setuptools import setup, find_packages
from rvtools_analyzer import __version__ as calver_version
import os

# Read requirements from requirements.txt
def read_requirements():
    with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
        return f.read().splitlines()

setup(
    name='avs-rvtools-analyzer',
    version=calver_version,
    description='A tool for analyzing RVTools data.',
    author='Ludovic Rivallain',
    author_email='ludovic.rivallain+pip@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'rvtools-analyzer=rvtools_analyzer.main:main'
        ]
    },
)
