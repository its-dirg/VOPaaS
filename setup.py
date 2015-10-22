from setuptools import setup

setup(
    name='VOPaaS',
    version='',
    packages=['vopaas', 'vopaas.backends', 'vopaas.frontends', 'vopaas.metadata_creation'],
    package_dir={'': 'src'},
    scripts=["src/vopaas/metadata_creation/make_vopaas_metadata.py"],
    url='',
    license='',
    author='DIRG',
    author_email='',
    description=''
)
