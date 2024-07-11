# Setup your environment
```
python -m venv .env
source .env/bin/activate
python install poetry
poetry install
```

# Build Release
```
docker build --target=runtime . -t matrix-bot-admin
```

# Execute Release
```
docker run --name bot-admin -v <path_to_config.toml>:/config.toml matrix-bot-admin
```