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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],

    keywords='pyiron',
    packages=find_packages(exclude=["*tests*", "*docs*", "*binder*", "*conda*", "*notebooks*", "*.ci_support*"]),
    install_requires=[
        'pyiron_base==0.5.31',
        'pyiron_atomistics==0.2.63',
        'ipywidgets==7.7.1',
        'matplotlib==3.6.3',
        'numpy==1.24.1',
        'pandas==1.5.3',
    ],
    cmdclass=versioneer.get_cmdclass(),
)
