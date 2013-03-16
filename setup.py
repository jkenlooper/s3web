from setuptools import setup, find_packages
import os

name = "s3web"
version = "0.1.2"

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name=name,
    version=version,
    author='Jake Hickenlooper',
    author_email='jake@weboftomorrow.com',
    description="Simple upload files to amazon s3 as a website",
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data = True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'boto',
        'progressbar',
    ],
    entry_points="""
    [console_scripts]
    s3web = s3web.script:main
    """,
)
