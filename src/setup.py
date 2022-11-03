from setuptools import setup, find_packages
setup(
    name='automatizacion_capitulo_1_IPC_INE',
    version='0.3',
    author='Luis Alfredo Alvarado Rodríguez',
    description='Automatizacion de extraccion de datos para el capitulo 1 del IPC.',
    long_description='',
    url='https://github.com/1u1s4/INE_IPC',
    keywords='development, setup, setuptools',
    python_requires='>=3.9',
    packages=find_packages(),
    py_modules=['datosipc','descriptoripc','funcionesjo','sqline'],
    install_requires=[
        'fredapi',
        'xlrd=1.2.0',
        'prettytable',
        'rpy2',
        'xlsxwriter',
        'pyodbc'
    ]
)