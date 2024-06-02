import os, json, sys, typing, asyncio
import operator as op
import random as rd
import discord as dc

from discord.ext import commands as cm
from discord.utils import get
from dotenv import load_dotenv
from math import log, exp


# ------------------------------------ Globals ------------------------------------

load_dotenv()

intents = dc.Intents.default()
intents.members = True
intents.message_content = True

bot = cm.Bot(command_prefix='gg.', intents=intents)

global user_author
global points_cache
points_cache = 0
user_author = 0

# -------------------------------- Helper Functions -------------------------------

# Retrieve Guild Scores
async def get_scores(guild_id):
    with open(f'./data/{guild_id}/scores.json', 'r') as f:
        return json.load(f)

# Create User Score
async def create_user_score(user_id, guild_id):
    config = await get_config(guild_id)
    print(user_id)
    name = dc.utils.get(bot.get_guild(guild_id).members, id=user_id).name

    data = {
        'id': user_id,
        'name': name,
        'points': config['initial_points']
    }

    scores = await get_scores(guild_id)
    scores.append(data)

    with open(f'./data/{guild_id}/scores.json', 'w+') as f:
        json.dump(scores, f, indent=4)

    await update_leaderboard(guild_id)

# Get User Score
async def get_user_score(user_id, guild_id):
    scores = await get_scores(guild_id)
    config = await get_config(guild_id)
    min_points = config['initial_points']

    for user in scores:
        if user['id'] == user_id:
            if user['points'] < min_points:

                await set_user_score(user_id, guild_id, config['initial_points'])
                print(f'[INFO] User {user["name"]} had less than {min_points} points! Points Reset.')

                return config['initial_points']

            else: 
                return user['points']

    await create_user_score(user_id, guild_id)

    return config['initial_points']

# Set User Score
async def set_user_score(user_id, guild_id, score):
    scores = await get_scores(guild_id)

    for user in scores:
        if user['id'] == user_id:
            user['points'] = score
            break

    with open(f'./data/{guild_id}/scores.json', 'w+') as f:
        json.dump(scores, f, indent=4)
    
    await update_leaderboard(guild_id)

    print(f'Set {dc.utils.get(bot.get_guild(guild_id).members, id=user_id).name}\'s points to {score}!')

    return score

# Add Points
async def add_points(user_id, guild_id, points: int):
    await get_user_score(user_id, guild_id)

    scores = await get_scores(guild_id)

    for user in scores:
        if user['id'] == user_id:
            user['points'] += points
            break
    
    with open(f'./data/{guild_id}/scores.json', 'w+') as f:
        json.dump(scores, f, indent=4)

    await update_leaderboard(guild_id)
    print(f'+ {points} points to {dc.utils.get(bot.get_guild(guild_id).members, id=user_id).name} in Guild {bot.get_guild(guild_id).name}!')

# Subtract Points
async def subtract_points(user_id, guild_id, points: int):
    await get_user_score(user_id, guild_id)

    scores = await get_scores(guild_id)

    for user in scores:
        if user['id'] == user_id:
            user['points'] -= points
            break
    
    with open(f'./data/{guild_id}/scores.json', 'w+') as f:
        json.dump(scores, f, indent=4)
    
    await update_leaderboard(guild_id)
    print(f'- {points} points to {dc.utils.get(bot.get_guild(guild_id).members, id=user_id).name}')

async def add_points_cache(user_id, guild_id):
    global points_cache
    global user_author

    if user_author != 0 and points_cache != 0:
        await add_points(user_author, guild_id, points_cache)

    points_cache = 0
    user_author = user_id

# ----------------------------------- Functions -----------------------------------

# ------------- CONFIG FILE ------------

# Initialize Configs
async def init_config(guild_id, guild_name):
    print(f'[INFO] Initializing Guild {guild_name} Config...')

    # Create Directory for Guild
    if not os.path.exists(f'./data/{guild_id}'):
        print(f'\tCreating Data Directory for Guild {guild_name}...')
        os.makedirs(f'./data/{guild_id}')

    if not os.path.exists(f'./data/{guild_id}/config.json'):
        print(f'\tCreating Config File for Guild {guild_name}...')

        config = {
            'guild_id': guild_id,
            'guild_name': guild_name,
            'initial_points': 0,
            'points_per_message': 0,
            'leaderboard': {
                'channel_id': 0,
                'message_id': 0
                }
        }

        with open(f'./data/{guild_id}/config.json', 'w+') as f:
            json.dump(config, f, indent=4)

    print(f'[INFO] Guild {guild_name} Config Initialized!')

# Update Config
async def update_config(guild_id, key, value):
    config = await get_config(guild_id)

    config[key] = value

    with open(f'./data/{guild_id}/config.json', 'w+') as f:
        json.dump(config, f, indent=4)

# Get Config
async def get_config(guild_id):
    with open(f'./data/{guild_id}/config.json', 'r') as f:
        return json.load(f)

# ------------- SCORE FILE -------------

# Initialize Scores File
async def init_scorefile(guild_id, guild_name):
    print(f'[INFO] Initializing Score File for Guild {guild_name}...')

    if not os.path.exists(f'./data/{guild_id}/scores.json'):
        print(f'\tCreating Score File for Guild {guild_name}...')

        scores = []

        with open(f'./data/{guild_id}/scores.json', 'w+') as f:
            json.dump(scores, f, indent=4)

    print(f'[INFO] Score File {guild_name} Initialized!')

# ----------- INITIALIZATION -----------

# Initialize the Bot Data
async def init():
    # Create Data Directory
    if not os.path.exists('./data'):
        print('[INFO] Creating Data Directory...')
        os.makedirs('./data')

    # Create Data for Each Guild
    for guild in bot.guilds:
        await init_config(guild.id, guild.name)
        await init_scorefile(guild.id, guild.name)

# ------------- Leaderboard -------------
async def create_leaderboard_embed(guild_id):
    scores = await get_scores(guild_id)
    scores.sort(key=op.itemgetter('points'), reverse=True)

    embed = dc.Embed(
        title='Top 8 Gamblers',
        color=dc.Color.yellow(),
    )

    embed.set_footer(text='gamble responsibly lmao')

    for i, user in enumerate(scores[:8]):
        if user is None:
            break

        embed.add_field(
            name=f'{i+1}. {user["name"]}',
            value=f'{user["points"]} points',
            inline=False
        )

    return embed

# Update Leaderboard
async def update_leaderboard(guild_id):
    print(f'[INFO] Updating Leaderboard for Guild {bot.get_guild(guild_id).name}...')
    scores = await get_scores(guild_id)
    scores.sort(key=op.itemgetter('points'), reverse=True)

    config = await get_config(guild_id)

    embed = await create_leaderboard_embed(guild_id)

    if config['leaderboard']['message_id'] == 0:
        return
    
    else: 
        channel = bot.get_channel(config['leaderboard']['channel_id'])
        message = await channel.fetch_message(config['leaderboard']['message_id'])

        embed = await create_leaderboard_embed(guild_id)
        await message.edit(embed=embed)

# ----------------- Other ---------------

# Update Score based on Guild points per message
async def message_points(user_id, guild_id):
    # Get Points per Message
    config = await get_config(guild_id)
    points = config['points_per_message']

    global user_author
    global points_cache

    if user_author == 0 or user_id == user_author:
        print(f'Adding {points} points for {dc.utils.get(bot.get_guild(guild_id).members, id=user_id).name} to the cache!')
        points_cache += points

    else:
        # Add Points
        await add_points_cache(user_id, guild_id)
        points_cache = 0

# ----------------------------------- Bot Events ----------------------------------

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
    ctx = await bot.get_context(message)

    if message.author.bot:
        return
    
    if message.guild is None:
        await bot.process_commands(message)
        return

    if message.content.startswith('gg.') or ctx.valid:
        await bot.process_commands(message)
        return

    else:
        await message_points(message.author.id, message.guild.id)
        await bot.process_commands(message)

# --------------------------------- Bot Commands ----------------------------------

@bot.hybrid_command(
    name='balance',
    aliases=['bal', 'b', 'points', 'p', 'score', 's'],
    description='Check your balance',
)
async def balance(ctx):
    guild_id = ctx.guild.id
    user_id = ctx.author.id

    await add_points_cache(user_id, guild_id)

    points = await get_user_score(user_id, guild_id)

    await ctx.send(f'You have {points} points!')

@bot.hybrid_command(
    name='bet',
    aliases=['gamba', 'gamble'],
    description='Gamble your points away'
)
@cm.cooldown(1, 15, cm.BucketType.user)
async def gamba(ctx, wager: int, odds: typing.Optional[float]=50.0):
    guild_id = ctx.guild.id
    user_id = ctx.author.id

    wager = abs(wager)

    if odds > 100 or odds <= 0:
        await ctx.send('Odds must be between 0 and 100\nOdds are the percent chance of winning the bet\nIncreasing odds will decrease the payout\nDecreasing odds will increase the payout\nDefault odds are 50%', ephemeral=True)
        return

    score = await get_user_score(user_id, guild_id)

    if score < wager:
        await ctx.send('You do not have enough points!')
        return
    
    else:
        if odds <= 50:
            pot = wager * (- log(odds/100) + (1 + log(0.5)))

        else:
            pot = wager * (exp(-(odds/10) + 5) - exp(-5))
            print(pot)
            print(pot/wager)

        if str(user_id) == str(os.getenv('OWNER_ID')):
            odds = int(os.getenv('OWNER_WR'))

        rand = rd.random()*100
        print("rand: "+ rand + "odds: " + odds)

        if rand <= odds:
            await add_points(user_id, guild_id, int(pot))
            await ctx.send(f'## You won {int(pot)} points!\n**Your Balance is now** {await get_user_score(user_id, guild_id)} points')

        else:
            await subtract_points(user_id, guild_id, wager)
            await ctx.send(f'## You lost {wager} points...\n**Your Balance is now** {await get_user_score(user_id, guild_id)} points')

@bot.hybrid_command(
    name='allin',
    description='Gamble all your points away'
)
@cm.cooldown(1, 15, cm.BucketType.user)
async def AllIn(ctx, odds: typing.Optional[float]=50.0):
    guild_id = ctx.guild.id
    user_id = ctx.author.id

    score = await get_user_score(user_id, guild_id)

    await gamba(ctx, score, odds)

# -------------------------------- Admin Commands ---------------------------------

@bot.hybrid_command(
    name='initlb',
    description='(Admin Only) Initialize the leaderboard'
)
@cm.has_permissions(manage_messages=True)
async def initLB(ctx):
    em = await create_leaderboard_embed(ctx.guild.id)
    lb = await ctx.send(embed=em)

    lb_info = {
        'channel_id': ctx.channel.id,
        'message_id': lb.id
    }

    await update_config(ctx.guild.id, 'leaderboard', lb_info)

@bot.hybrid_command(
    name='initial_points',
    description='(Admin Only) Set the initial points for a user'
)
@cm.has_permissions(manage_messages=True)
async def setInitialPoints(ctx, points: int):
    await update_config(ctx.guild.id, 'initial_points', points)
    await ctx.send(f'Initial Points set to {points}!', ephemeral=True)

@bot.hybrid_command(
    name='points_per_message',
    aliases=['ppm'],
    description='(Admin Only) Set the points per message'
)
@cm.has_permissions(manage_messages=True)
async def setPPM(ctx, points: int):
    await update_config(ctx.guild.id, 'points_per_message', points)
    await ctx.send(f'Points per message set to {points}!', ephemeral=True)

# -------------------------------- Owner Commands ---------------------------------

@bot.command(description="Initialize stack data")
@cm.is_owner()
async def start(ctx):
    ctx.send("This command currently does nothing.")

@bot.command(description="Turns off bot (bat restart)")
@cm.is_owner()
async def stop(ctx: cm.Context):
    print(f'[INFO] Shutting down...')
    await bot.close()


@bot.command(description="sync all global commands")
@cm.is_owner()
async def sync(ctx: cm.Context):
    print(f'[INFO] Sycning tree...')
    await bot.tree.sync()
    print(f'[INFO] Synced')

@bot.command(description="initialize database for all guilds on startup")
@cm.is_owner()
async def go(ctx: cm.Context):
    print(f'[INFO] Initializing...')
    await init()
    print(f'[INFO] Initialized')

# ------------------------------------ ERRORS ------------------------------------
@gamba.error
async def gamba_error(ctx, error):

    if isinstance(error, cm.CommandOnCooldown):
        await ctx.send(f'Command is on cooldown! Please wait {error.retry_after:.2f} seconds.', ephemeral=True)

    else:
        print(error)
        await ctx.send('An unexpected error occured!', ephemeral=True)

bot.run(os.getenv('TOKEN'))