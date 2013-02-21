from setuptools import setup

setup(name='pql',
      version='0.1.1',
      description='A python expression to MongoDB query translator',
      author='Alon Horev',
      author_email='alon@horev.net',
      url='https://github.com/alonho/pql',
      classifiers = ["Development Status :: 3 - Alpha",
                     "Intended Audience :: Developers",
                     "Programming Language :: Python :: 2.6",
                     "Programming Language :: Python :: 2.7",
                     "Programming Language :: Python :: 3.3",
                     "Operating System :: POSIX :: Linux",
                     "Operating System :: MacOS :: MacOS X"],
      license='BSD',
      # I know it's bad practice to not specify a pymongo version, but we only
      # require the bson.ObjectId type, It's safe to assume it won't change (famous last words)
      install_requires=['pymongo'], 
      py_modules=['pql'])