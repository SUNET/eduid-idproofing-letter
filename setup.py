from setuptools import setup, find_packages


version = '0.1.2b0'

requires = [
        'eduid-msg>=0.10.0',
        'eduid-userdb>=0.0.4',
        'eduid-common>=0.1.1',
        'Flask==0.10.1',
        'Flask-WTF==0.12',
        'gunicorn==19.4.1',
        'Pillow==3.0.0',
        'xhtml2pdf==0.0.6',
]

test_requires = []

testing_extras = test_requires + [
    'nose==1.2.1',
    'coverage==3.6',
    'nosexcover==1.0.8',
]

long_description = open('README.txt').read()

setup(name='eduid-idproofing-letter',
      version=version,
      description="POC Flask api micro service",
      long_description=long_description,
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='NORDUnet A/S',
      author_email='',
      url='https://github.com/SUNET/',
      license='gpl',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      test_suite="eduiddashboard",
      extras_require={
          'testing': testing_extras,
      },
      entry_points="""
      """,
      )
