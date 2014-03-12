import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='countrywhere',
    version='1.0',
    packages=['countrywhere'],
    package_data={
        'countrywhere': ['country_world.json']
        },
    include_package_data=True,
    license='MIT License',
    description='Python library to look up country from lat / long offline',
    long_description=README,
    url='https://github.com/pegler/pycountrywhere',
    author='Matt Pegler',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Localization',
    ],
)
