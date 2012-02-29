import os
from setuptools import setup, find_packages
from setuptools.command.develop import develop as STDevelopCmd

class DevelopCmd(STDevelopCmd):
    def run(self):
        # add in requirements for testing only when using the develop command
        self.distribution.install_requires.extend([
            'nose',
        ])
        STDevelopCmd.run(self)

class ProdCmd(STDevelopCmd):
    pass

cdir = os.path.abspath(os.path.dirname(__file__))
readme_rst = open(os.path.join(cdir, 'readme.rst')).read()
changelog_rst = open(os.path.join(cdir, 'changelog.rst')).read()

required_packages = []
try:
    import json
except ImportError:
    required_packages.append('simplejson')

setup(
    name='JSONRPCBase',
    version='0.1.2',
    description='Simple JSON-RPC service without transport layer',
    long_description= readme_rst + '\n\n' + changelog_rst,
    classifiers=[
        'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    author='Randy Syring',
    author_email='rsyring@gmail.com',
    url='https://bitbucket.org/rsyring/jsonrpcbase',
    license='MIT',
    py_modules=['jsonrpcbase'],
    install_requires=required_packages,
    include_package_data=True,
    zip_safe=False,
    cmdclass = {'develop': DevelopCmd, 'prod': ProdCmd}
)
