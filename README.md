<p align="center">
  <a href="https://github.com/nschloe/tiptop"><img alt="tiptop" src="https://raw.githubusercontent.com/nschloe/tiptop/gh-pages/tiptop.svg" width="60%"/></a>
  <p align="center">Command-line system monitoring.</p>
</p>

[![PyPi Version](https://img.shields.io/pypi/v/tiptop.svg?style=flat-square)](https://pypi.org/project/tiptop/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/tiptop.svg?style=flat-square)](https://pypi.org/project/tiptop/)
[![GitHub stars](https://img.shields.io/github/stars/nschloe/tiptop.svg?style=flat-square&logo=github&label=Stars&logoColor=white)](https://github.com/nschloe/tiptop)
[![Downloads](https://pepy.tech/badge/tiptop/month?style=flat-square)](https://pepy.tech/project/tiptop)

<!--[![PyPi downloads](https://img.shields.io/pypi/dm/tiptop.svg?style=flat-square)](https://pypistats.org/packages/tiptop)-->

[![Discord](https://img.shields.io/static/v1?logo=discord&logoColor=white&label=chat&message=on%20discord&color=7289da&style=flat-square)](https://discord.gg/Z6DMsJh4Hr)
[![Donate](https://img.shields.io/badge/-Donate-yellow?logo=paypal&style=flat-square)](https://paypal.me/nschloe)
[![Sponsor](https://img.shields.io/badge/-Sponsor-red?logo=github&style=flat-square)](https://github.com/sponsors/nschloe)
[![Coffee](https://img.shields.io/badge/-Buy%20me%20a%20Coffee-grey?logo=Ko-fi&style=flat-square)](https://ko-fi.com/nschloe)

[![gh-actions](https://img.shields.io/github/workflow/status/nschloe/tiptop/ci?style=flat-square)](https://github.com/nschloe/tiptop/actions?query=workflow%3Aci)
[![LGTM](https://img.shields.io/lgtm/grade/python/github/nschloe/tiptop.svg?style=flat-square)](https://lgtm.com/projects/g/nschloe/tiptop)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)

tiptop is a command-line system monitoring tool in the spirit of
[top](<https://en.wikipedia.org/wiki/Top_(software)>). It displays various
interesting system stats, graphs it, and works on Linux and macOS.

Install and run with

<!--pytest-codeblocks: skip-->

```sh
pip install tiptop
tiptop
```

<p align="center">
<img alt="screenshot" src="https://raw.githubusercontent.com/nschloe/tiptop/gh-pages/screenshot.png" width="100%"/>
</p>

For all options, see

```sh
tiptop -h
```

<!--pytest-codeblocks: expected-output-->

```
usage: tiptop [-h] [--version] [--net NET]

Command-line system monitor.

optional arguments:
  -h, --help         show this help message and exit
  --version, -v      display version information
  --net NET, -n NET  network interface to display (default: auto)
```

tiptop uses [Textual](https://github.com/willmcgugan/textual/) for layouting and [psutil](https://github.com/giampaolo/psutil) for fetching system data.

Other top alternatives in alphabetical order:

- [bashtop](https://github.com/aristocratos/bashtop), [bpytop](https://github.com/aristocratos/bpytop), [btop](https://github.com/aristocratos/btop) (which inspired tiptop)
- [bottom](https://github.com/ClementTsang/bottom)
- [Glances](https://github.com/nicolargo/glances)
- [gtop](https://github.com/aksakalli/gtop)
- [htop](https://github.com/htop-dev/htop)

See [here](https://github.com/nschloe/stargraph#command-line-system-monitoring)
for a comparison by GitHub stars.
