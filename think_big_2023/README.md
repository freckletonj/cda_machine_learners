# Think Big 2023

## Goals:

  * a single discord channel that the bot responds to, so we don't get flooded in other channels.
  * Should we open the bot up to private messages?
  * The bots:
    * /t2midjourney <prompt> is there a simple way to intercept these messages and have my paid account mirror the request? That could be cool.
    * /t2i <prompt> text 2 image, StableD
    * /i2i <url> <prompt>, img 2 img, StableD
    * /t2t <prompt>, ChatGPT
    * /t2v <prompt> some text 2 vid model, I have yet to experiment here
    * /t2langchain if anyone has any cool ideas

## Usage

### Setup
Copy the `.env_sample` file to `.env` and fill in the values.

```sh
cp .env_sample .env
```

Make sure you have Docker and Docker Compose installed.

```sh
docker-compose build
```

### Running

To run the bot in the background, use the following command:
```sh
docker-compose up -d
```
Remove the -d flag to run in the foreground and see logs.

### Stopping
To stop a container that is running in the background, use the following command:
```sh
docker-compose down
```



# OLD

Just get a copy of the `TOKEN` and go for it!

```sh

TOKEN=$(cat .discord_token) python src/main.py

```
