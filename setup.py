from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='ghrepo',
    version='1.0',
    author='Lucian Cooper',
    url='https://github.com/luciancooper/ghrepo',
    description='Github API Command Line Tool',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='git utility',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    install_requires=['pydecorator'],
    packages=[],
    scripts=['bin/ghrepo'],
    #entry_points={ 'console_scripts': ['ghrepo=ghrepo:main'] },
)
