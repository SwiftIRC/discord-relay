# IRC <-> Discord Relay

## Configuring

Create a `.env` file using the following example:

```ini
TOKEN = sekrit.token.goes.here
SERVER = fiery.swiftirc.net
PORT = 6697
NICK = Discord
CHANNELS = '{"#rshelp": 306269746280529920}'
```

## Running

```bash
python3 main.py
```
