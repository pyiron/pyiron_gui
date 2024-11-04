"""
Setuptools based setup module
"""
from setuptools import setup, find_packages

import versioneer

setup(
    name='pyiron_gui',
    version=versioneer.get_version(),
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
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12'
    ],

    keywords='pyiron',
    packages=find_packages(exclude=["*tests*", "*docs*", "*binder*", "*conda*", "*notebooks*", "*.ci_support*"]),
    install_requires=[
        'pyiron_base==0.10.4',
        'pyiron_atomistics==0.6.14',
        'ipywidgets==8.1.5',
        'matplotlib==3.9.2',
        'nbconvert==7.16.4',
        'nbformat==5.10.4',
        'numpy==2.1.3',
        'pandas==2.2.3',
    ],
    cmdclass=versioneer.get_cmdclass(),
)
