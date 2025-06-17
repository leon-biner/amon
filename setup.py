import setuptools
from distutils.core import setup

setup(
    name='amon',
    version='0.0.0',
    description='wind farm blackbox',
    packages=['amon'],
    entry_points={
        'console_scripts' : ['amon=amon.src.main:main']
    },
    install_requires= []
)