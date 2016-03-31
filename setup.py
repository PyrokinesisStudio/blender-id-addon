from distutils.command.bdist import bdist
from distutils.command.install import install
from setuptools import setup, find_packages


class BlenderAddonBdist(bdist):
    """Ensures that 'python setup.py bdist' creates a zip file."""

    def initialize_options(self):
        super().initialize_options()
        self.formats = ['zip']
        self.plat_name = 'addon'  # use this instead of 'linux-x86_64' or similar.


class BlenderAddonInstall(install):
    """Ensures the module is placed at the root of the zip file."""

    def initialize_options(self):
        super().initialize_options()
        self.prefix = ''
        self.install_lib = ''


setup(
    cmdclass={'bdist': BlenderAddonBdist,
              'install': BlenderAddonInstall},
    name='blender_id',
    description='The Blender ID addon allows authentication of users.',
    version='1.0.0',
    author='Francesco Siddi, Sybren A. Stüvel',
    author_email='francesco@blender.org',
    packages=find_packages('.'),
    data_files=[('blender_id', ['README.md'])],
    scripts=[],
    url='https://developer.blender.org/diffusion/BIA/',
    license='GNU General Public License v2 or later (GPLv2+)',
    platforms='',
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',
        'Environment :: Plugins',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
    ],
    zip_safe=True,
)
