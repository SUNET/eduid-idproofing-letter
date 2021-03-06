from setuptools import setup, find_packages


version = '0.2.2b4'

requires = [
    'Flask==0.10.1',
    'Pillow>=3.0.0',
    'xhtml2pdf==0.1b3',
    'eduid-msg>=0.10.0',
    'eduid-userdb>=0.1.0b0',
    'eduid-common==0.2.1b5',
    'kombu<4',
    'marshmallow==2.13.5',
    'flask-apispec==0.4.0',
    'gunicorn==19.4.1',
]

test_requires = [
    'mock==1.3.0',
]

testing_extras = test_requires + [
    'nose==1.3.7',
    'coverage==4.0.3',
    'nosexcover==1.0.10',
]

long_description = open('README.md').read()

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
      test_suite="idproofing_letter",
      extras_require={
          'testing': testing_extras,
      },
      entry_points={}
      )
