import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='pylotoncycle',
    version='0.5.2',
    description='Module to access your Peloton workout data',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/justmedude/pylotoncycle',
    author='Vikram Adukia',
    author_email='github@fireitup.net',
    license='BSD',
    packages=['pylotoncycle'],
    install_requires=['requests'],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3'
    ]
)
