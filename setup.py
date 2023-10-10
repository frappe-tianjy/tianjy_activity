from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in tianjy_activity/__init__.py
from tianjy_activity import __version__ as version

setup(
	name="tianjy_activity",
	version=version,
	description="Tianjy Activity",
	author="guigu",
	author_email="guigu",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
