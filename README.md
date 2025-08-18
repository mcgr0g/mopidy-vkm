# mopidy-vkm

[![CI build status](https://img.shields.io/github/actions/workflow/status/mcgr0g/mopidy-vkm/ci.yml)](https://github.com/mcgr0g/mopidy-vkm/actions/workflows/ci.yml)
[![Test coverage](https://img.shields.io/codecov/c/gh/mcgr0g/mopidy-vkm)](https://codecov.io/gh/mcgr0g/mopidy-vkm)

Mopidy extension for vkm.
It enables secure playback of music from VKontakte (vk.com). The project provides a fully-featured backend, VK-aware library and playback providers, a minimal web login UI, and strict credential handling — all packaged for easy deployment via Docker Compose on a NAS.


## Installation

Install by running:

```sh
python3 -m pip install mopidy-vkm
```

See https://mopidy.com/ext/vkm/ for alternative installation methods.


## Configuration

Before starting Mopidy, you must add configuration for
mopidy-vkm to your Mopidy configuration file:

```ini
[vkm]
enabled = true
# Optional: Specify a user agent string for VK API requests
# If not specified, a random user agent will be selected
user_agent =

# Path to store sensitive credentials (tokens, etc.)
# This file will be created with secure permissions (600)
sensitive_cache_path = /var/lib/mopidy/vkm/sensitive.json

# Optional: Path to cache downloaded tracks
# If specified, tracks will be cached for offline playback
cache_path = /var/lib/mopidy/vkm/cache

# Optional: Path to save downloaded tracks permanently
# If specified, tracks will be saved for future use
saved_path = /var/lib/mopidy/vkm/saved

# Optional: Audio quality (low, medium, high)
# Default is medium
quality = medium
```


## Usage

### Authentication

1. Start Mopidy with the VKM extension enabled.
2. Open a web browser and navigate to `http://your-mopidy-server:port/vkm`.
3. Enter your VK login (email or phone) and password.
4. If required, complete CAPTCHA or two-factor authentication.
5. Once authenticated, you can use VK Music in Mopidy.

### Features

- **Browse**: Browse your VK music library, including saved tracks, playlists, and recommendations.
- **Search**: Search for tracks, artists, and albums on VK.
- **Playback**: Play tracks from VK with reliable streaming.
- **Offline Mode**: If configured, tracks can be cached for offline playback.

### Security

- All sensitive data (tokens, credentials) is stored securely with strict file permissions.
- Passwords are never stored, only authentication tokens.
- User-Agent rotation helps prevent account locks.

## Project resources

- [Source code](https://github.com/mcgr0g/mopidy-vkm)
- [Issues](https://github.com/mcgr0g/mopidy-vkm/issues)
- [Releases](https://github.com/mcgr0g/mopidy-vkm/releases)


## Development

### Set up development environment

Clone the repo using, e.g. using [gh](https://cli.github.com/):

```sh
gh repo clone mcgr0g/mopidy-vkm
```

Enter the directory, and install dependencies using [uv](https://docs.astral.sh/uv/):

```sh
cd mopidy-vkm/
uv sync
```

### Running tests

To run all tests and linters in isolated environments, use
[tox](https://tox.wiki/):

```sh
tox
```

To only run tests, use [pytest](https://pytest.org/):

```sh
pytest
```

To format the code, use [ruff](https://docs.astral.sh/ruff/):

```sh
ruff format .
```

To check for lints with ruff, run:

```sh
ruff check .
```

To check for type errors, use [pyright](https://microsoft.github.io/pyright/):

```sh
pyright .
```

### Setup before first release

Before the first release, you must [enable trusted publishing on
PyPI](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
so that the `release.yml` GitHub Action can create the PyPI project and publish
releases to PyPI.

When following the instructions linked above, use the following values in the
form at PyPI:

- Publisher: GitHub
- PyPI project name: `mopidy-vkm`
- Owner: `mcgr0g`
- Repository name: `mopidy-vkm`
- Workflow name: `release.yml`
- Environment name: `pypi` (must match environment name in `release.yml`)

### Making a release

To make a release to PyPI, go to the project's [GitHub releases
page](https://github.com/mcgr0g/mopidy-vkm/releases)
and click the "Draft a new release" button.

In the "choose a tag" dropdown, select the tag you want to release or create a
new tag, e.g. `v0.1.0`. Add a title, e.g. `v0.1.0`, and a description of the changes.

Decide if the release is a pre-release (alpha, beta, or release candidate) or
should be marked as the latest release, and click "Publish release".

Once the release is created, the `release.yml` GitHub Action will automatically
build and publish the release to
[PyPI](https://pypi.org/project/mopidy-vkm/).


## Credits

- Original author: [Ronnie McGrog](https://github.com/mcgr0g)
- Current maintainer: [Ronnie McGrog](https://github.com/mcgr0g)
- [Contributors](https://github.com/mcgr0g/mopidy-vkm/graphs/contributors)
