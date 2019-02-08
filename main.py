#!/usr/bin/env python3
import yaml
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions, has_role
import os
import aiohttp
from cogs.utils import checks

config = yaml.safe_load(open('config.yml'))
token = yaml.safe_load(open('token.yml'))
bot = commands.Bot(config['prefix'],description='')

bot.loaded_cogs = []

def load_cogs():
    for extension in os.listdir('cogs'):
        if os.path.isfile('cogs/{}'.format(extension)) and extension.endswith('.py'):
            try:
                bot.load_extension("cogs." + extension[:-3])
                bot.loaded_cogs.append(extension[:-3])
            except Exception as e:
                print(e)
            else:
                print('Loaded extension {}'.format(extension)) 

load_cogs()

@checks.check_permissions_or_owner(administrator=True)
@bot.command()
async def list_cogs(ctx):
    cog_list = commands.Paginator(prefix='', suffix='')
    cog_list.add_line('Loaded:')
    for cog in bot.loaded_cogs:
        cog_list.add_line('- ' + cog)

    for page in cog_list.pages:
        await ctx.send(page)

@checks.check_permissions_or_owner(administrator=True)
@bot.command()
async def load(ctx, cog):
    if cog in bot.loaded_cogs:
        return await ctx.send('Extension already loaded.')
    try:
        bot.load_extension('cogs.{}'.format(cog))
    except Exception as exc:
        await ctx.send('```{}\n{}```'.format(type(exc).__name__, exc))
        await ctx.send('⚠ Loading the extension failed.')
    else:
        bot.loaded_cogs.append(cog)
        await ctx.send('The extension was loaded successfully.')

@checks.check_permissions_or_owner(administrator=True)
@bot.command()
async def unload(ctx, cog):
    if cog not in bot.loaded_cogs:
        return await ctx.send('This extension has not been loaded yet!')
    bot.unload_extension('cogs.{}'.format((cog)))
    bot.loaded_cogs.remove(cog)
    await ctx.send('The extension has been disabled successfully.')

@checks.check_permissions_or_owner(administrator=True)
@bot.command()
async def shutdown(ctx):
        await ctx.send("Stopping.")
        print("Stopped by {}.".format(ctx.author.name))
        await bot.close()
        await bot.logout()
        await bot.wait_closed()
        os.exit(0)

@checks.check_permissions_or_owner(administrator=True)
@bot.command()
async def reload(ctx, cog):
    if cog not in bot.loaded_cogs:
        return await ctx.send('This extension has not been loaded yet!')
    bot.unload_extension('cogs.{}'.format((cog)))
    try:
        bot.load_extension('cogs.{}'.format(cog))
        await ctx.send('The extension was reloaded successfully.')
    except Exception as exc:
        await ctx.send('```{}\n{}```'.format(type(exc).__name__, exc))
        await ctx.send('⚠ Loading the extension failed.')
    
@shutdown.error
@unload.error
@load.error
@reload.error
async def cmderror(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the required permissions for this.")

@bot.event
async def on_ready():
    print('Logged in as: ' + bot.user.name)
    bot.session = aiohttp.ClientSession(loop=bot.loop, headers={"User-Agent": "Botaww"})

bot.run(token["token"])