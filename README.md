# pyfoobar

[![PyPi Version](https://img.shields.io/pypi/v/pyfoobar.svg?style=flat-square)](https://pypi.org/project/pyfoobar/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/pyfoobar.svg?style=flat-square)](https://pypi.org/project/pyfoobar/)
[![GitHub stars](https://img.shields.io/github/stars/nschloe/pyfoobar.svg?style=flat-square&logo=github&label=Stars&logoColor=white)](https://github.com/nschloe/pyfoobar)
[![PyPi downloads](https://img.shields.io/pypi/dm/pyfoobar.svg?style=flat-square)](https://pypistats.org/packages/pyfoobar)

[![gh-actions](https://img.shields.io/github/workflow/status/nschloe/pyfoobar/ci?style=flat-square)](https://github.com/nschloe/pyfoobar/actions?query=workflow%3Aci)
[![CircleCI](https://img.shields.io/circleci/build/github/nschloe/pyfoobar/main.svg?style=flat-square)](https://circleci.com/gh/nschloe/pyfoobar/tree/main)
[![travis](https://img.shields.io/travis/nschloe/pyfoobar.svg?style=flat-square)](https://travis-ci.com/nschloe/pyfoobar)
[![codecov](https://img.shields.io/codecov/c/github/nschloe/pyfoobar.svg?style=flat-square)](https://codecov.io/gh/nschloe/pyfoobar)
[![LGTM](https://img.shields.io/lgtm/grade/python/github/nschloe/pyfoobar.svg?style=flat-square)](https://lgtm.com/projects/g/nschloe/pyfoobar)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)


A Python project template that highlights some best practices in Python packaging. Can
be used as a [GitHub
template](https://github.blog/2019-06-06-generate-new-repositories-with-repository-templates/)
for your new Python project.

### Best practices

* The **name** of the Git repository should be the PyPi name of the package and should
  be what you type as `import mypackagename`. That means no hyphens in package
  names!

* Your package should be a **one-trick pony**. Nobody wants to install a huge toolbox if
  all they need is the image converter in it.

* Choose a **license** for your code and provide a `LICENSE[.txt]` in the root level of
  your package as well as a statement in your main README.
  [choosealicense.com](https://choosealicense.com/) can help you make a decision.

* Use **linting and formatting**, include those in your integration tests.
    - [black](https://github.com/psf/black) is a formatter that I like because you
      cannot configure it -- black is black.
    - Good linters are [flake8](http://flake8.pycqa.org/en/latest/) and
      [pylint](https://www.pylint.org/).
    - [isort](https://pypi.org/project/isort/) sorts your imports.
    - [pre-commit](https://pre-commit.com/) has gained some popularity. It runs your
      linters and formatters on every commit. Not more "lint fix" commits.

* Once you have tests in order, make sure they are executed with every git push.
  Popular **CI services** that run your tests are [GitHub
  Actions](https://github.com/features/actions), [Travis CI](https://travis-ci.org/),
  and [CircleCI](https://circleci.com/). This repository contains the config files for
  each of them.

* Make sure that **nobody can push to main**. On GitHub, go to Settings -> Branches ->
  Add rule and select _Require status checks to pass before merging_ and _Include
  administrators_. Development happens in pull requests, this makes sure that nobody --
  including yourself -- ever accidentally pushes something broken to main.

* Use a tool for measuring **test coverage**. [codecov](https://about.codecov.io/) is one, and
  your CI provider submits the data to it.

* If you have CI set up, want to show test coverage, or advertise
  the availability on PyPi, do so using a **badge** at the top of your README. Check out
  [shields.io](https://shields.io/) for what's available.

* Include [**contributing guidelines**](CONTRIBUTING.md) and a [**code of
  conduct**](CODE_OF_CONDUCT.md) (edit to add appropriate
  [enforcement](CODE_OF_CONDUCT.md#enforcement) contacts or [use a
  template](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-code-of-conduct-to-your-project))
  to help foster a community.

### What you can do with this template

First run
```
find . -type f -print0 -name "*.py" -o -name "*.yml" | xargs -0 sed -i 's/pyfoobar/your-project-name/g'
```
and rename the folder `src/pyfoobar` to customize the name.

There is a simple [`justfile`](https://github.com/casey/just) that can help you with
certain tasks:
  * Run `just format` to apply formatting.
  * Run `just lint` to check formatting and style.
  * Run `just publish` to
     - tag your project on git (`just tag`)
     - upload your package to PyPi (`just upload`)

    After publishing, people can install your package with
    ```
    pip install pyfoobar
    ```

### Testing
To run the pyfoobar unit tests, check out this repository and do
```
tox
```

### License
pyfoobar is published under the [MIT license](https://en.wikipedia.org/wiki/MIT_License).
