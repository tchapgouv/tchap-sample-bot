# Setup your environment
```
python -m venv .env
source .env/bin/activate
python install poetry
poetry install
```

# Provide a config.toml file at the root of the project
```
homeserver = "<your matrix server https://matrix.…>"

bot_username = "<your username someone@beta.gouv.fr>"
bot_password = "<your password>"
```

# Build Release
```
docker build --target=runtime . -t matrix-bot-admin
```

# Execute Release
```
docker run --name bot-admin -v <path_to_config.toml>:/data/config.toml matrix-bot-admin
```
