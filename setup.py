from setuptools import setup

setup(
    name='hypothesis-pb',
    packages=['hypothesis_protobuf'],
    platforms='any',
    version='1.0.0',
    description='Hypothesis extension to allow generating protobuf messages matching a schema.',
    author='H. Chase Stevens / Curata Inc.',
    author_email='chase@curata.com',
    license='MIT',
    install_requires=[
        'hypothesis>=3.4.2',
        'protobuf>=3.3.0,<4.0.0',
    ],
    tests_require=['pytest>=3.1.2', 'future>=0.16.0'],
    extras_require={'dev': ['pytest>=3.1.2', 'future>=0.16.0']},
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ]
)
