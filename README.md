# seot-agent

PoC code for the Sharing Economy of Things platform.

## Requirements

- Python 3.5.x or later
- pip

### Node-specific requirements

- `SenseHatSource`
    - RaspberryPi with Sense HAT
    - Requires the running user to be in the following groups: `input`,
      `gpio`, `i2c` and `spi`
- `PiCamSource`
    - RaspberryPi with camera module
    - Requires the running user to be in the `video` group
- `ZMQSource/ZMQSink`
    - libzmq (optional)
- `DockerTransformer`
    - docker
    - Requires the running user to be able to run docker commands without sudo

## How to run

### From source

1. Copy `config.yml.sample` to `~/.config/seot/config.yml` and adjust config
   values.
2. Optionally, use direnv and virtualenv to create an isolated environment.
3. Install dependencies: `pip3 install -r requirements.txt`
4. Launch SEoT Agent: `python3 -m seot.agent`

### From docker image

1. `docker login registry.ais.cmc.osaka-u.ac.jp`
2. `docker run -v <path/to/config>:/etc/seot/config.yml registry.ais.cmc.osaka-u.ac.jp/tis/seot-agent`

Additionally, mount the docker socket `-v /var/run/docker.sock:/var/run/docker.sock`
to use `DockerTransformer`

## How to package

1. Build wheel file: `python setup.py bdist_wheel`
2. Wheel file is generated under `dist/`.
3. (Run `pip install dist/*.whl` to install wheel)

## Recommended tools during development

- [MongoDB Compass](https://www.mongodb.com/products/compass?jmp=docs): For
  exploring data stored in MongoDB.
