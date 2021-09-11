from setuptools import setup, find_packages

setup(
    name='rcedit',
    version='0.1',
    packages=find_packages(include=['rcedit']),
    install_requires=[
        'requests>=2.26.0',
    ]
)
