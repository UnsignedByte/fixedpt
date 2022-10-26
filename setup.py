from setuptools import setup

from fixedpt import __version__

setup(
	name='fixedpt',
	version=__version__,

	url='https://github.com/UnsignedByte/fixedpt',
	author='Edmund Lam',
	
	py_modules=['fixedpt'],
	install_requires=[
		'numpy',
	]
)
