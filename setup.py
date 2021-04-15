"""
Setuptools based setup module
"""
from setuptools import setup, find_packages


setup(
    name='pyiron_gui',
    version='0.0.1',
    description='Repository for GUI plugins to the pyiron IDE.',
    long_description='http://pyiron.org',

    url='https://github.com/pyiron/pyiron_gui',
    author='Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department',
    author_email='siemer@mpie.de',
    license='BSD',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],

    keywords='pyiron',
    packages=find_packages(exclude=["*tests*"]),
    install_requires=[
        'pyiron_base==0.2.9',
        'pyiron_atomistics==0.2.10',
        'ipywidgets==7.6.3',
        'matplotlib==3.4.1',
        'mendeleev==0.7.0',
        'numpy==1.20.2',
        'pandas==1.2.4',
    ]
)
