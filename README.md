# Sunny Day Discord Bot
Baseball Discord bot that can post up-to-date scores, lineups, and home runs. Uses webscraping techniques to scrape baseball data from various websites in real time to respond to commands.

## Overview
This bot has three primary functionalities: retrieving scores, lineups, and home runs.

### Scores
To retrieve all scores for the current day, use the command `>scores`. This will post an image for each matchup today.
![Scores Example](https://github.com/bjhammack/sunny-day-discord-bot/blob/main/scores/example_score.png)

To retrieve the score for a single team for the current day, use the command `>score {team's 3-letter abbreviation}`. This will post a single image of that team's matchup, if they have a matchup for today.

### Lineups
To retrieve all lineups for the current day, use the command `>lineups`. This will post an image for each matchup's lineups today.
![Lineups Example](https://github.com/bjhammack/sunny-day-discord-bot/blob/main/lineups/example_lineup.png)

To retrieve the lineup for a single team for the current day, use the command `>lineup {team's 3-letter abbreviation}`. This will post a single image of that team's lineup, if they have a game for today.
![Lineup Example](https://github.com/bjhammack/sunny-day-discord-bot/blob/main/lineups/team_example_lineup.png)

### Home Runs
Between 11am and midnight CT, every 15 minutes this bot will scrape the five most recent home runs, compare these against previous home runs, and post new home runs that have occurred.
![Home Run Example](https://github.com/bjhammack/sunny-day-discord-bot/blob/main/lineups/home_run_example.png)

## Setup
Several steps should be taken prior to activating this bot to ensure your system will be able to run it without error.

### OS Compatibility
This bot was designed to work on a Linux server and therefore has some features that are only compatible with Linux. With several changes (removing the daemonization process), the program can be altered to work on Windows or Mac.

### Web Browser Availability
This bot uses [Selenium](https://selenium-python.readthedocs.io) to scrape data from the internet. Selenium uses a webdriver to utlize a system's existing web browser to simulate a user accessing the website. The bot is designed to work with a Chrome based browser (Chrome, Chromium, Vivaldi, etc.), but can be altered to work with Firefox, Safari, or Opera.

To use a different browser, make the necessary changes in `baseball_spider.py`'s `_prep_driver()` function. Otherwise, ensure that a chrome-based browser is downloaded to its default location (`/usr/bin/chromium-browser` for Chromium on Ubuntu).

### .env
You will need to create a .env file in your working directory. This file needs to contain four things:
<ul>
	<li>DISCORD_TOKEN={The token for your bot}</li>
	<li>DISCORD_GUILD={The name of the guild your bot will be hosted on}</li>
	<li>DISCORD_TARGET_CHANNEL={The channel ID you want the bot to post scheduled updates}</li>
	<li>DISCORD_NOTIFICATION_CHANNEL={The channel ID where the bot should notify that updates have occurred}</li>
</ul>

### requirements.txt
Be sure to install all libraries in requirements.txt via `pip install -r requirements.txt`

## Runing the Bot
To run the bot simply type `python bot.py` while in the working directory of this project. If all the steps were properly followed in the setup section, you should see the bot connect to the webdriver and then begin waiting.

### Logs
Log files are generated for this bot and stored in the logs folder. They will log every action the bot performs, every error that occurs, and the time these events took place.

A new log file is generated for each time the bot is spun up. An example of a log can be found [here](https://github.com/bjhammack/sunny-day-discord-bot/blob/main/logs/example_log.log)
