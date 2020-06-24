from setuptools import setup

__version__ = '0.5.1'

setup(name='pql',
      version=__version__,
      description='A python expression to MongoDB query translator',
      author='Alon Horev',
      author_email='alon@horev.net',
      url='https://github.com/alonho/pql',
      classifiers = ["Development Status :: 3 - Alpha",
                     "Intended Audience :: Developers",
                     "Programming Language :: Python :: 3.3",
                     "Programming Language :: Python :: 3.5",
                     "Programming Language :: Python :: 3.6",
                     "Programming Language :: Python :: 3.7",
                     "Programming Language :: Python :: 3.8",
                     "Operating System :: POSIX :: Linux",
                     "Operating System :: MacOS :: MacOS X"],
      license='BSD',
      # I know it's bad practice to not specify a pymongo version, but we only
      # require the bson.ObjectId type, It's safe to assume it won't change (famous last words)
      install_requires=['pymongo',
                        'python-dateutil'],
      packages=['pql'])
