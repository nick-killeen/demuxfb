# setuptools script
# Use `python setup.py sdist` to compile to dist/

import setuptools
with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='demuxfb',
    # Date of Facebook 'Download Your Information' data archive creation this
    # is built against.
    version='2020.12.15',
    author='Nicholas Killeen',
    author_email='nicholas.killeen2@gmail.com',
    description='Parse Facebook Conversation Archives',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nick-killeen/demuxfb',
    license='MIT',
    package_dir={'': 'src'},
    packages=setuptools.find_packages(include=['demuxfb', 'demuxfb.*']),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    keywords='facebook messages data',
    python_requires='>=3.8',
)
