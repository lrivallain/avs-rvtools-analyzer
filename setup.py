from setuptools import setup, find_packages

# Manually set the CalVer version
calver_version = '2025.4.2'

setup(
    name='avs-rvtools-analyzer',
    version=calver_version,
    description='A tool for analyzing RVTools data.',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'pandas',
        'openpyxl'
    ],
    entry_points={
        'console_scripts': [
            'rvtools-analyzer=rvtools_analyzer.main:main'
        ]
    },
)
