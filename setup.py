from distutils.core import setup

import sphere

with open('README.md', 'r') as fp:
    LONG_DESC = fp.read()


setup(
    name='sphere',
    version=sphere.__version__,
    url='https://github.com/ttake-spalab/sphere',
    author='T. Takeuchi',
    author_email='t.take.spalab@gmail.com',
    description='Simple python I/O for NIST-SPHERE file',
    long_description=LONG_DESC,
    keywords=['SPHERE', 'NIST'],
    py_modules=['sphere'],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
