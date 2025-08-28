from setuptools import setup, find_packages

setup(
    name='displacement_forecast',
    version='0.1',
    description='IDMC Displacement Forecasting',
    url='http://github.com/ChrisFairless/displacement_forecast',
    author='Chris Fairless',
    author_email='chrisfairless@hotmail.com',
    license='OSI Approved :: GNU Lesser General Public License v3 (GPLv3)',
    python_requires=">=3.9,<3.12",
    install_requires=[
        'climada',
        'climada_petals',
        'beautifulsoup4',
    ],
    packages=find_packages(),
    include_package_data=False
)
