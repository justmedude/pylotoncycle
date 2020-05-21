from setuptools import setup

setup(
    name='pylotoncycle',
    version='0.1',
    description='Module to access your peloton workout data',
    url='https://github.com/justmedude/pylotoncycle',
    author='Vikram Adukia',
    author_email='github@fireitup.net',
    license='MIT',
    packages=['pylotoncycle'],
    install_requires=['requests'],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3'
    ]
)
