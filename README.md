Ce projet est basé sur le Tchap `matrix-admin-bot` : https://github.com/tchapgouv/matrix-admin-bot

# Configuration de l'environnement

- Python 3.11+ est requis
- Poetry est requis
```
python -m venv .env
source .env/bin/activate
python install poetry
poetry install
```

# Le fichier `config.toml`

Il est nécessaire de créer un fichier `config.toml` contenant les informations de connexion de votre bot.
Ce fichier contenant des informations sensibles, il n'est pas gitté.
```
homeserver = "<your matrix server https://matrix.…>"

bot_username = "<your username someone@beta.gouv.fr>"
bot_password = "<your password>"
```

# Construire l'image du container Docker
```
docker build --target=runtime --tag tchap-sample-bot .
```

# Démarrer le container Docker
L'option `--rm` supprime le container à la fin de l'exécution.
L'option `--env PYTHONBUFFERED=1` permet d'avoir les sorties de python dans la console.
```
docker run --rm --env PYTHONBUFFERED=1 --volume <path-to-your-local-config-file>:/data/config.toml tchap-sample-bot
```

# Structure du projet

Le projet utilise `Poetry`, un gestionnaire de dépendances pour Python : https://python-poetry.org/docs

À la racine du projet se trouvent les fichiers :
- `Dockerfile` : le script de création du conntainer Docker du bot
- `config.toml` : le fichier des paramètres de connexion du bot (non gitté)
- `pyproject.toml` : le fichier de dépendances du projet, utilisé par Poetry lors de la construction de l'image Docker
- `scripts/commands` : le dossier contenant les implémentations des commandes supportées par le bot

## Démarrage du bot
Le fichier `pyproject.toml` définit le point d'entrée du programme à : `scripts.startbot:main`
C'est à cet endroit que : 
- la configuration du bot est chargée via `BotConfig`
- le bot est créé via `ValidateBot`
- le bot est lancé via `bot.run()`

## Les commandes implémentées dans le bot
Dans le fichier `startbot.py`, la variable `COMMANDS` liste les commandes accessibles (c'est les noms des classes correspondantes suffixées par `Command`).

Les classes implémentant les actions sont dans `scripts/commands`.

Dans cet exemple : 
- `get_hour` : le bot renvoie l'heure actuelle avec la commande `!get_hour`
- `get_rss` : le bot renvoit un flux RSS formaté avec la commande `!get_rss <URL du flux RSS souhaité>`

# La commande `get_rss`
Elle est implementée dans le fichier `scripts/commands/get_rss.py` par la classe `GetHourCommand`.

La variable `KEYWORD` contient le nom de la commande (qui sera préfixée par `!` pour être reconnue comme une commande).
Ce préfixe est standard mais peut être customisé (voir https://code.peren.fr/MatMaul/tchapbot/-/tree/tchapadmin).

La fonction `needs_secure_validation` peut renvoyer `TRUE` si le lancement de l'action nécessite une validation (saisie de `YES` voire d'un code OTP).
Dans cet exemple, ce niveau de sécurisation n'est pas abordé. Il est utilisé en interne chez Tchap.

Si une commande `!get_rss <args>` est saisie, elle sera à une nouvelle instance de la classe `GetRssCommand`.

1. un `MessageEventParser` est créé à l'instanciation pour ce client dans cette room, pour le message qui vient d'être reçu
2. si le message est envoyé par le bot, il est ignoré par la commande `do_not_accept_own_message`
3. les éventuels arguemnts de la commande sont récupérés par `args = event_parser.command(self.KEYWORD).split()`
4. la méthode asynchrone `execute` prend le relai et fait le traitement réel (dans notre cas, récupérer le contenu du flux RSS et le mettre en forme)
5. la méthode `execute` finit par envoyer un message dans la room contenant le flux RS formaté, via l'appel `send_text_message`
