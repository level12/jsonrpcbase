from setuptools import setup, find_packages

fh = open('README.rst', 'rb')
long_desc = fh.read()
fh.close()

required_packages = []
try:
    import json
except ImportError:
    required_packages.append('simplejson')

setup(name='JSONRPCBase',
      version='0.1.1',
      description='Simple JSON-RPC service without transport layer',
      long_description = long_desc,
      classifiers=[
        'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
      ],
      author='Randy Syring',
      author_email='rsyring@gmail.com',
      url='https://bitbucket.org/rsyring/jsonrpcbase',
      license='MIT',
      py_modules=['jsonrpcbase'],
      install_requires=required_packages,
      include_package_data=True,
      zip_safe=False,
     )
