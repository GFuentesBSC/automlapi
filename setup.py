from distutils.core import setup

VERSION = "0.149"

setup(
  name = 'automlapi',
  packages = ['automlapi'],
  version = VERSION,
  license='MIT',
  description = 'api for the AutoML project',
  author = 'Raul Garcia',
  author_email = 'raulgfuentes97@gmail.com',
  url = 'https://github.com/GFuentesBSC/automlapi',
  download_url = f'https://github.com/GFuentesBSC/automlapi/archive/v{VERSION}.tar.gz',
  keywords = ['AUTOML', 'BOTO3', 'AWS'],   # Keywords that define your package best
  install_requires=[
          'tqdm',
          'PyPDF2',
          'boto3',
          'botocore',
          'PyMySQL'
          # 'mysqlclient'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)
