# setup.py
from setuptools import setup, find_packages

# Read the contents of requirements.txt
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='litewebagent',
    version='0.1.1',
    packages=find_packages(),
    include_package_data=True,
    author='Danqing Zhang',
    author_email='danqing.zhang.personal@gmail.com',
    python_requires='>=3.6',
    install_requires=required,
)
