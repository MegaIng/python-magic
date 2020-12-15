

from distutils import sysconfig
from distutils.core import setup

site_packages_path = sysconfig.get_python_lib()
setup(
    name='rewrite_magic',
    packages=['rewrite_magic'],
    package_dir={'': 'src'}
)
