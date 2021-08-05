from distutils.core import setup

import sphere

with open('README.md', 'r') as fp:
    LONG_DESC = fp.read()


setup(
    name='sphere',
    version=sphere.__version__,
    author='t-take',
    author_email='t.take.spalab@gmail.com',
    description='NIST SPHERE file I/O',
    long_description=LONG_DESC,
    keywords=['SPHERE', 'NIST'],
    py_modules=['sphere'],
)
