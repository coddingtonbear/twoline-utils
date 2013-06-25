import os
import multiprocessing

from setuptools import setup, find_packages

with open(
    os.path.join(
        os.path.dirname(__file__),
        'requirements.txt'
    )
) as f:
    required = f.read().splitlines()

setup(
    name='twoline-utils',
    version='0.7.7',
    url='http://bitbucket.org/latestrevision/twoline-utils/',
    description='Utils for http://bitbucket.org/latestrevision/twoline/',
    author='Adam Coddington',
    author_email='me@adamcoddington.net',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
    install_requires=required,
    packages=find_packages(),
    entry_points={'console_scripts': [
        'tlu = twoline_utils.cmdline:run_from_cmdline']},
    test_suite='nose.collector',
    tests_require=[
        'nose',
    ]
)
