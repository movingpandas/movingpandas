# Contributing to MovingPandas

Whether you are a novice or experienced software developer, all contributions
and suggestions are welcome!

## Getting Started

If you are looking to contribute to the *MovingPandas* codebase, the best place to
start is the [GitHub "issues" tab](https://github.com/anitagraser/movingpandas/issues).
This is also a great place for filing bug reports and making suggestions for
ways in which we can improve the code and documentation.

## Contributing to the Codebase

The code is hosted on [GitHub](https://github.com/anitagraser/movingpandas),
so you will need to use [Git](http://git-scm.com/) to clone the project and make
changes to the codebase. Once you have obtained a copy of the code, you should
create a development environment that is separate from your existing Python
environment so that you can make and test changes without compromising your
own work environment.

### Development library installation

To setup you should install moving pandas in editable mode with:

```bash
pip install -e .
pip install -r dev-requirements.txt
```

Alternately you can install the development requirements in a single line with:

```bash
pip install -e ".[dev]"
``` 

### Run the tests

Before submitting your changes for review, make sure to check that your changes
do not break any tests. There are two methods to run tests:

1. To run tests in the current development environment run `pytest` or 
   `pytest -cov=movingpandas` to check code coverage for the unit tests.
2. To run more complete integration tests in multiple environments you can use `tox`
   instead. **Note** this assumes you are developing in an Anaconda development
   environment. Also, be warned running in this way takes *much* longer (and will
   create 4 new Anaconda environments to work in).

### Raising Pull Requests

Once your changes are ready to be submitted, make sure to push your changes to
your fork of the GitHub repo before creating a pull request.  We will review
your changes, and might ask you to make additional changes before it is finally
ready to merge. However, once it's ready, we will merge it, and you will have
successfully contributed to the codebase!
