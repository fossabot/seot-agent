# seot-agent
[![build status](https://titan.ais.cmc.osaka-u.ac.jp/tis/seot-agent/badges/master/build.svg)](https://titan.ais.cmc.osaka-u.ac.jp/tis/seot-agent/commits/master)

PoC code for the Sharing Economy of Things platform.

## Requirements

- Python 3.5.x or later
- pip
- zmq
- libsodium
- (Optional) virtualenv
- (Optional) direnv (2.5.0 or later)
- (Optional) pythonz


### Nodes

- `DockerTransformer`
    - Requires docker
    - Requires running user to be in the `docker` group
- `SenseHatSource`
    - Requires RaspberryPi and Sense Hat hardware
    - Requires running user to be in the following groups: `video`, `input`,
        `gpio`, `i2c` and `spi`

## How to run

1. Copy `config.yml.sample` to `~/.config/seot/config.yml` and adjust config
   values.
2. Optionally, use direnv and virtualenv to create an isolated environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Launch SEoT Agent: `python -m seot.agent`

## How to package

1. Build wheel file: `python setup.py bdist_wheel`
2. Wheel file is generated under `dist/`.
3. (Run `pip install dist/*.whl` to install wheel)

## Recommended tools during development

- [MongoDB Compass](https://www.mongodb.com/products/compass?jmp=docs): For
  exploring data stored in MongoDB.
