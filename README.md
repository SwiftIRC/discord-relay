# IRC <-> Discord Relay

## Configuring

Create a `.env` file using the following example:

```ini
TOKEN = sekrit.token.goes.here
SERVER = fiery.swiftirc.net
PORT = 6697
NICK = Discord
CHANNELS = '{"#rshelp": 306269746280529920}'
SASL_USERNAME = account
SASL_PASSWORD = sekrit.password
```

`SASL_USERNAME` and `SASL_PASSWORD` are optional; see [SASL](#sasl) below.

The IRC connection always uses TLS and verifies the server's certificate
against the system CA store, so `SERVER` must be a hostname that the
certificate is issued for.

## SASL

SASL logs the relay in to its services account during connection, before it
joins any channels.

1. Register an account for the relay with the network's services (typically
   `/msg NickServ REGISTER <password> <email>` while using the relay's nick).
2. Set `SASL_USERNAME` to the account name (usually the registered nick) and
   `SASL_PASSWORD` to its password. Set both or neither; setting only one is a
   startup error.
3. Start the relay. On success it connects and joins its channels as usual.

The relay uses the SASL PLAIN mechanism. If the server doesn't support SASL, or
rejects the credentials, the relay logs the reason (for example
`SASL authentication failed: SASL authentication failed`) and exits with
status 1 rather than running unauthenticated or retrying bad credentials. Check
the account name and password, then restart it.

`.env` now holds a password: it's already in `.gitignore`, but also make it
readable only by the user that runs the relay (`chmod 600 .env`).

## Running

```bash
python3 main.py
```
