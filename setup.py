from setuptools import setup

execfile('src/s3web/_version.py')
setup(name="s3web",
    version=__version__,
    author='Jake Hickenlooper',
    author_email='jake@weboftomorrow.com',
    description="Simple upload files to amazon s3 as a website",
    packages=['s3web'],
    package_dir={'': 'src'},
    install_requires=[
      'boto',
      'progressbar',
      ],
    include_package_data = True,
    entry_points=("""
      [console_scripts]
      s3web=s3web.script:main
      """)
    )
