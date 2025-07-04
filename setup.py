from setuptools import find_packages, setup

setup(
    name='flitsr',
    packages=find_packages(),
    package_data={
        'flitsr': ['py.typed'],
    },
)
