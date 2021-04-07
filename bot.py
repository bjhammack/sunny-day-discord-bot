from baseball_spider import Spider
from daemonize import Daemonize
import datetime as dt
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from functools import partial
import glob
import logging
import os
import random
import time
import traceback

def main(logger):
    # Initialzing a Spider() intance to get the data
    spider = Spider()

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD = os.getenv('DISCORD_GUILD')
    TARGET_CHANNEL = int(os.getenv('DISCORD_TARGET_CHANNEL'))
    NOTIFICATION_CHANNEL = int(os.getenv('DISCORD_NOTIFICATION_CHANNEL'))

    bot = commands.Bot(command_prefix='>')

    @bot.command(name='lineups')
    async def lineups(ctx):
        '''
        Upon the ">lineup" command, posts an image of all matchup lineups for today.
        '''
        try:
            logger.info('Fetching lineups.')
            spider.generate_lineup_images()
            logger.info('Lineups retrieved.')

            logger.info('Sending message(s).')
            messages = [await ctx.send(file=discord.File(file)) for file in glob.iglob(r'lineups\*.png')]
        except:
            error = traceback.format_exc()
            logger.error(error)

    @bot.command(name='lineup')
    async def lineup(ctx, team=None):
        '''
        Upon the ">lineup <team abbrv>" command, posts the text of that team's lineup for today.
        '''
        try:
            logger.info(f'Fetching {team}\'s lineup.')
            team = team.upper()
            lineup = spider.format_team_lineup(team)
            logger.info(f'Retrieved {team}\'s lineup.')

            if len(lineup) < 1:
                logger.info(f'No lineup for {team}.')
                await ctx.send(f'No lineup for {team} for today.')
            else:
                logger.info('Sending message(s).')
                await ctx.send(lineup)
        except:
            error = traceback.format_exc()
            logger.error(error)

    @tasks.loop(hours=1.0)
    async def scheduled_lineups():
        '''
        Posts today's matchup lineup images for every team at 1100, 1700, 2000 CT.
        '''
        try:
            channel = bot.get_channel(TARGET_CHANNEL)
            notification_channel = bot.get_channel(NOTIFICATION_CHANNEL)
            if channel:
                hour = dt.datetime.now().hour
                if hour in (11,17,20):
                    logger.info('Fetching scheduled lineups')
                    spider.generate_lineup_images()
                    logger.info('Lineups scheduled retrieved.')

                    logger.info('Sending message(s).')
                    messages = [await channel.send(file=discord.File(file)) for file in glob.iglob(r'lineups\*.png')]
                    await notification_channel.send('Lineups update in #sunny-day')
        except:
            error = traceback.format_exc()
            logger.error(error)

    @tasks.loop(hours=1.0)
    async def scheduled_scores():
        '''
        Posts today's score images for every team at 1100, 1700, 2000 CT.
        '''
        try:
            channel = bot.get_channel(TARGET_CHANNEL)
            notification_channel = bot.get_channel(NOTIFICATION_CHANNEL)
            if channel:
                hour = dt.datetime.now().hour
                if hour in (16,21,0):
                    logger.info('Fetching scheduled scores')
                    spider.generate_score_images()
                    logger.info('Scheduled scores retrieved.')

                    logger.info('Sending message(s).')
                    messages = [await channel.send(file=discord.File(file)) for file in glob.iglob(r'scores\*.png')]
                    await notification_channel.send('Scores update in #sunny-day')
        except:
            error = traceback.format_exc()
            logger.error(error)
            
    @bot.command(name='scores')
    async def scores(ctx):
        '''
        Upon the command ">scores", posts today's scores images for every team for today.
        '''
        try:
            logger.info('Fetching scores.')
            scores = spider.generate_score_images()
            logger.info('Scores retrieved.')

            logger.info('Sending message(s).')
            messages = [await ctx.send(file=discord.File(file)) for file in glob.iglob(r'scores\*.png')]
        except:
            error = traceback.format_exc()
            logger.error(error)

    @bot.command(name='score')
    async def score(ctx, team):
        '''
        Upon the command ">score <team abbr>", posts the score image of that team's matchup for today.
        '''
        try:
            logger.info(f'Fetching score for {team}.')
            team = team.upper()
            score = spider.generate_team_score_image(team)
            logger.info(f'Score retrieved for {team}.')

            logger.info('Sending message(s).')
            messages = [await ctx.send(file=discord.File(file)) for file in glob.iglob(r'scores\*.png')]
        except:
            error = traceback.format_exc()
            logger.error(error)

    @tasks.loop(minutes=15.0)
    async def scheduled_homers():
        '''
        Checks for new home runs every 15 minutes, posting new homers when they are found.
        '''
        try:
            channel = bot.get_channel(TARGET_CHANNEL)
            if channel:
                hour = dt.datetime.now().hour
                if hour not in range(0,11):
                    logger.info('Checking for new homers.')
                    homers = spider.get_homers()

                    if len(homers) > 0:
                        logger.info('Posting new homers.')
                        messages = [await channel.send(f'{homer}') for homer in homers]
        except:
            error = traceback.format_exc()
            logger.error(error)

    @scheduled_lineups.before_loop
    async def before():
        '''
        Wait to begin the scheduled lineup posts until the top of the hour.
        '''
        try:
            start_time  = dt.datetime.now() + dt.timedelta(hours=1)
            start_time = dt.datetime(start_time.year, start_time.month,start_time.day,start_time.hour,0,0)
            td = start_time - dt.datetime.now()
            logger.info(f'Waiting to begin scheduled lineups/scores loops for {td.seconds} seconds.')
            time.sleep(td.seconds)
            await bot.wait_until_ready()
        except:
            error = traceback.format_exc()
            logger.error(error)

    scheduled_lineups.start()
    scheduled_scores.start()
    scheduled_homers.start()

    bot.run(TOKEN)

def prep_logger():
    '''
    Setting log file for this instance of the bot.
    '''
    log_dir = 'logs/'
    logs = glob.glob(log_dir+'bot*.log')
    if len(logs) == 0:
        new_log = 1
    else:
        try:
            new_log = max([int(i.split('\\')[-1].split('_')[1][0]) for i in logs]) + 1
        except:
            new_log = 1
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    f_handler = logging.FileHandler(f'logs/bot_{new_log}.log')
    f_format = logging.Formatter('[%(asctime)s] - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)
    keep_fds = [f_handler.stream.fileno()]

    return logger, keep_fds

if __name__ == '__main__':
    logger, keep_fds = prep_logger()
    #main(logger)
    pid = '/tmp/sunny_day_botd.pid'
    daemon = Daemonize(app='sunny_day_botd', pid=pid, action=partial(main, logger=logger), keep_fds=keep_fds)
    daemon.start()