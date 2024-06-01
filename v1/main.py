import os, json, sys, typing
import operator as op
import random as rd
import discord as dc

from discord.ext import commands as cm
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()

intents = dc.Intents.default()
intents.members = True
intents.message_content = True

bot = cm.Bot(command_prefix='gg.', intents=intents)

async def init():
    print('Initializing...')

    # Create ./data directory if it doesn't exist
    if not os.path.exists('./data'):
        os.mkdir('./data')
        print('\tCreated data directory')

    # Create ./data/{guild.id}/leaderboard.json if it doesn't exist
    print ('\tChecking guilds...')
    for guild in bot.guilds:
        # Create ./data/{guild.id} directory if it doesn't exist
        if not os.path.exists(f'./data/{guild.id}'):
            os.mkdir(f'./data/{guild.id}')
            print(f'\t\tCreated directory for {guild.name}!')

        # Create ./data/{guild.id}/leaderboard.json if it doesn't exist
        if not os.path.exists(f'./data/{guild.id}/leaderboard.json'):
            with open(f'./data/{guild.id}/leaderboard.json', 'w') as f:
                json.dump([], f, indent=4)

            print(f'\t\tCreated leaderboard file for {guild.name}!')

        if not os.path.exists(f'./data/{guild.id}/config.json'):

            config = {
                'points_per_message': 10,
                'leaderboard': {
                    'channel_id': 0,
                    'message_id': 0
                    }
                }
            
            with open(f'./data/{guild.id}/config.json', 'w') as f:
                json.dump(config, f, indent=4)

            print(f'\t\tCreated config file for {guild.name}!')

    print('Initialization complete!')

async def add_points(user_id: int, guild_id: int):
    with open(f'./data/{guild_id}/config.json', 'r') as f:
        config = json.load(f)

    with open(f'./data/{guild_id}/leaderboard.json', 'r') as f:
        data = json.load(f)

    points = config['points_per_message']

    for user in data:
        if user['id'] == user_id:
            user['points'] += points
            break

    with open(f'./data/{guild_id}/leaderboard.json', 'w') as f:
        json.dump(data, f, indent=4)

async def subtract_points(user_id: int, points: int, guild_id: int):
    with open(f'./data/{guild_id}/leaderboard.json', 'r') as f:
        data = json.load(f)

    for user in data:
        if user['id'] == user_id:
            user['points'] -= points
            break

    with open(f'./data/{guild_id}/leaderboard.json', 'w') as f:
        json.dump(data, f, indent=4)
        
async def getScores(guild_id: int):
    with open(f'./data/{guild_id}/leaderboard.json', 'r') as f:
        data = json.load(f)

    return data

async def update_lb_message(guild_id: int):
    with open(f'./data/{guild_id}/config.json', 'r') as f:
        config = json.load(f)

    with open(f'./data/{guild_id}/leaderboard.json', 'r') as f:
        data = json.load(f)

    data.sort(key=op.itemgetter('points'), reverse=True)

    lb = 'Leaderboard:\n'
    for i, user in enumerate(data):
        lb += f'{i+1}. <@{user["id"]}> - {user["points"]} points\n'

    channel = bot.get_channel(config['leaderboard']['channel_id'])
    message = await channel.fetch_message(config['leaderboard']['message_id'])

    await message.edit(embed=lb)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await init()

@bot.event
async def on_guild_join(guild):
    print(f'Joined guild {guild.name}!')
    await init()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    else:
        add_points(message.author.id, message.guild.id)

    await bot.process_commands(message)

@bot.hybrid_command(
    name='balance',
    aliases=['bal', 'points', 'p', 'b'],
    description='Check your balance',
)
async def balance(ctx):
    guild_id = ctx.guild.id
    user_id = ctx.author.id

    with open(f'./data/{guild_id}/leaderboard.json', 'r') as f:
        data = json.load(f)

    for user in data:
        if user['id'] == user_id:
            ctx.send(f'You have {user["points"]} points!')

@bot.hybrid_command(
    name='initlb',
    description='(Admin Only) Initialize the leaderboard'
)
@cm.has_permissions(administrator=True)
async def initLB(ctx):
    await getScores(ctx.guild.id)
    with open(f'./data/{ctx.guild.id}/config.json', 'r') as f:
        config = json.load(f)

@bot.hybrid_command(
    name='bet',
    aliases=['gamba', 'gamble'],
    description='Gamble your points away'
)
async def gamba(ctx, points: int, odds: typing.Optional[float]=0.5):
    guild_id = ctx.guild.id
    user_id = ctx.author.id

    with open(f'./data/{guild_id}/leaderboard.json', 'r') as f:
        data = json.load(f)

    for user in data:
        if user['id'] == user_id:
            if user['points'] < points:
                await ctx.send('You do not have enough points!')
                return

            user['points'] -= points

            if rd.random() < odds:
                user['points'] += points * 2
                await ctx.send(f'You won {points * 2} points!')
            else:
                await ctx.send(f'You lost {points} points!')

            break

    with open(f'./data/{guild_id}/leaderboard.json', 'w') as f:
        json.dump(data, f, indent=4)
    


bot.run(os.getenv('TOKEN'))