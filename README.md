# napari-AFMReader

<div align="center">

[![PyPI version](https://badge.fury.io/py/napari-afmreader.svg)](https://badge.fury.io/py/napari-afmreader)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/napari-afmreader)
[![Code style:
Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-456789.svg)](https://github.com/psf/flake8)
[![codecov](https://codecov.io/gh/AFM-SPM/napari-afmreader/branch/dev/graph/badge.svg)](https://codecov.io/gh/AFM-SPM/napari-afmreader)
[![pre-commit.ci
status](https://results.pre-commit.ci/badge/github/AFM-SPM/napari-afmreader/main.svg)](https://results.pre-commit.ci/latest/github/AFM-SPM/napari-afmreader/main)
[![fair-software.eu](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B-yellow)](https://fair-software.eu)

</div>
<div align="center">

[![Downloads](https://static.pepy.tech/badge/napari-afmreader)](https://pepy.tech/project/napari-afmreader)
[![Downloads](https://static.pepy.tech/badge/napari-afmreader/month)](https://pepy.tech/project/napari-afmreader)
[![Downloads](https://static.pepy.tech/badge/napari-afmreader/week)](https://pepy.tech/project/napari-afmreader)

</div>
<div align="center">

| [Installation](#installation) | [Usage](#usage) | [Licence](#licence) | [Citation](#citation) |

</div>

A [Napari](https://napari.org/) plugin to read in Atomic Force Microscopy (AFM) files using
[AFMReader](https://github.com/AFM-SPM/AFMReader.git).

You can drag and drop your favourite AFM image files directly into the Napari viewer to use the awesome tools the image
analysis community have developed over at the [Napari Hub](https://www.napari-hub.org/) to analyse your images using
open-source software and a GUI!

<div align="center">
| File Extension | Supported by AFMReader | Description              |
| -------------- | ---------------------- | ------------------------ |
| `.asd`         | ✅                     | High-speed AFM format.   |
| `.gwy`         | ✅                     | Gwyddion saved format.   |
| `.ibw`         | ✅                     | Igor binary-wave format. |
| `.jpk`         | ✅                     | JPK instruments format.  |
| `.spm`         | ✅                     | Bruker spm format.       |
| `.stp`         | ✅                     | Homemade stp format.     |
| `.top`         | ✅                     | Homemade top format.     |
| `.topostats`   | ✅                     | topostats output format. |
</div>

## Installation

### Via Napari-Hub

This software should be installable directly from Napari!

All you need to do is:

1. [Install Napari](https://napari.org/stable/tutorials/fundamentals/installation.html) into an environment.
2. Open Napari by typing `napari` into your command line with your Napari environment activated.
   ```bash
   napari
   ```

3. Go to `Plugins` > `Install/Uninstall Plugins`, and search for `napari-afmreader`.

### Via Git

Occasionally the Napari-Hub version of `napari-AFMReader` may not be the most up-to-date. This is when you might want
to install both the most up-to-date `AFMReader` and `napari-AFMReader` versions via Git.

`napari-AFMReader` has been designed to need minimal maintenance, with most of the new file type additions being solely
added to AFMReader.

1. With [Git installed](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) on your machine, clone both the
   `AFMReader` and `napari-AFMReader` repositories:

   ```bash
   git clone https://github.com/AFM-SPM/AFMReader.git
   ```

   ```bash
   git clone https://github.com/AFM-SPM/napari-AFMReader.git
   ```

2. Activate your Python environment (e.g. Conda) and install the dependencies for each - make sure that the `AFMReader`
   dependency is installed second to overwrite the possibly outdated `afmreader` package!

   ```bash
   cd napari-AFMReader
   pip install .
   cd ..
   ```

   ```bash
   cd AFMReader
   pip install .
   ```

3. Now when you open Napari via the `napari` command, it should use the latest version of `AFMReader`, and
   `napari-AFMReader`.

   ```bash
   napari
   ```

## Usage

This package should be fairly straight-forward and intuitive to use, requiring you to:

1. Drag and drop your supported AFM file into the Napari Viewer.

2. Type in the name of the channel you would like to use. You may not need to specify a channel for e.g. `.stp`, or the
   channel may refer to image key in the `.napari-afmreader` file.\*.

   \*_Possible channel names will not appear at first due to the order in which AFMReader processes an image. Thus,
   when provided with an non-existent channel name, the dialogue box will then return a list of possible channels to
   choose from._

## Licence

**This software is licensed as specified by the [GPL License](COPYING) and [LGPL License](COPYING.LESSER).**

## Citation

Please use the [Citation File Format](https://citation-file-format.github.io/) which is available in this repository.