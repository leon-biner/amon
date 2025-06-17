import setuptools
from distutils.core import setup

setup(
    name='amon',
    version='0.0.0',
    description='wind farm blackbox',
    packages=setuptools.find_packages(),
    package_data={
        "amon": ["data/*"],  # or just ["data/*"]
    },
    entry_points={
        'console_scripts' : ['amon=amon.src.main:main']
    },
    install_requires= []
)