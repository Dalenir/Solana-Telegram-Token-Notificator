

## Solana Wallet Token Tracker ...in Telegram

### What is it?
- Telegram bot that tracks transactions in Solana blockchain
- Mostly token and pumpfun tuned
- Resembles **Solana Ray | Wallet TrackerSolana Ray | Wallet Tracker** bot
  - and I think you are better to use it, lol
- Docker-based and self-contained, just make .env, build and run
- No rate-limiting
- Pretty fast
- Informative and you can always change some text if you want
- Customisible. Just drop the Birdeye API key and hope that DEXScreener will have all data you need with some small rate.

### What it will need:
- Helius API key (currently **$49/mo**) [can be trial]
- Birdeye API key (currently **$99/mo**) [optional]

### What it can do:
- Track your solana transacrions
- Even fresh Pumpfun tokens (market data is 1min. max after creation)
- It can be used to even make some people pay you for better access, but I think you must add 1-2 lines of code for this

### What it can't do:
- Be faster and cooler than beforementioned bot that was builded not by the one hungry developer
- Get all your fresh memecoin market data reliably under the 1 minute (1m+ is stable)

## How to run?
> You must have docker installed on your system ofc
### 1. Make an .env file like this (or copy .env.example) at root
###### .env
```dotenv
# Docker
PROJECT_NAME="NamelessTelegramSolana"

# Database
DB_PORT=5432
DB_NAME="wallet_tracker_bot"
DB_USERNAME="wallet_tracker_bot"
DB_PASSWORD="Please_made_password_*&@*^$*(@<<#MAL"

# Bot
ADMIN_ID=123
BOT_TOKEN="AAA"
MODE=MAIN

# Cache
REDIS_INNER_PORT=2769

# Connections
HELIUS_API_KEY=AAA
# -- not required --
BIRDEYE_API_KEY=AAA
```

### 2. Build image
```shell
docker compose build
```

### 2. Generate Migrations
```shell
docker compose run --rm telegram alembic revision --autogenerate -m 'NAME'
```
### 3. Run migrations
```shell
docker compose run --rm telegram alembic upgrade head ;  docker compose stop database;
```
### 4. Build image and run it

---
### Planned features and fixes
Do not hope that this will be soon, tho

1. Cleanup
2. Logging (sorry)
3. More customisible texts for the transaction
4. Remake for pure solana rpc calls and some basic notifications for this

---
> #### For any questions, feel free to contact me as you wish, I very bad at social networking.
