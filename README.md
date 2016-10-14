# seot-agent

PoC code for the Sharing Economy of Things platform.

## Requirements

- Python 3.5.x or later
- pip
- OpenSSL
- (Optional) virtualenv
- (Optional) direnv (2.5.0 or later)
- (Optional) pythonz

## How to run

1. Optionally, use direnv and virtualenv to create an isolated environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Launch SEoT Agent: `python -m seot.agent`

## Recommended tools during develop

- [msgpack-tools](https://github.com/zweifisch/msgpack-tool): For parsing and
    building seot-dpp messages. Use in conjunction with openssl.
- [mock-server](https://github.com/tomashanacek/mock-server): For mocking the
    seot-server.
