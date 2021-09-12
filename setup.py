from setuptools import setup, find_packages

with open('README.rst', 'r') as fh:
    long_description = fh.read()

exec(open('bruker_utils/_version.py').read())

setup(
    name='bruker_utils',
    version=__version__,
    description='bruker_utils: Helper functions for handling Bruker NMR data.',
    author='Simon Hulse',
    author_email='simon.hulse@chem.ox.ac.uk',
    url='https://github.com/5hulse/bruker_utils',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        'Programming Language :: Python :: 3.6',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Topic :: Scientific/Engineering',
    ],
    install_requires=["numpy"],
    python_requires='>=3.6',
    include_package_data=True,
    packages=find_packages(),
)
