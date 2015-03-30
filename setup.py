# -*- encoding: utf8 -*-
from setuptools import setup, find_packages

import os

setup(
    name="tblib",
    version="1.0.0",
    url='https://github.com/ionelmc/python-tblib',
    download_url='',
    license='BSD',
    description="Traceback fiddling library.",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    author='Ionel Cristian Mărieș',
    author_email='contact@ionelmc.ro',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Debuggers',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    install_requires=[
        'six',
    ]
)
