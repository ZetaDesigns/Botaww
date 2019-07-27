from discord.ext import commands
import discord
import os
import io
import math
from PIL import Image
from cogs.utils import checks

class Emote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def collect_image(self, ctx, url, static=False):
        data = io.BytesIO()
        length = 0
        async with self.bot.session.get(url) as resp:
            while True:
                dat = await resp.content.read(16384)
                if not dat:
                    break
                length += len(dat)
                if length > 8 * 1024 * 1024 * 16:
                    return None, None
                data.write(dat)

        data.seek(0)
        im = Image.open(data)
        return im

    def process_image(self, image):
        image_file_object = io.BytesIO()
        image.save(image_file_object, format="png")
        image_file_object.seek(0)
        return image_file_object

    async def aiosessionget(self, url):
        data = await self.bot.session.get(url)
        if data.status == 200:
            b_data = await data.read()
            # print(f"Data from {url}: {byte_data}")
            return b_data
        else:
            print(f"HTTP Error {data.status} "
                  f"while getting {url}")
    
    @commands.group(aliases=['emoji'])
    async def emote(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('You need to specify an emotetype.')
            await ctx.send_help(ctx.command)

    @emote.command()
    async def noemote(self, ctx, url=None):
        if not url:
            if ctx.message.attachments:
                image = await self.collect_image(ctx, ctx.message.attachments[0].url, True)
            else:
                return await ctx.send("❌ You need to provide a url or have an attachment on your message!")
        else:
            try:
                image = await self.collect_image(ctx, url, True)
            except ValueError:
                return await ctx.send("❌ You need to provide a url or have an attachment on your message!")
        width, height = image.size
        noimage = Image.open(os.getcwd() + "/resources/no.png")
        if width > height:
            noimage.thumbnail((height,height))
            image.paste(noimage, (int((width - height) / 2), 0), noimage)
        else:
            noimage.thumbnail((width,width))
            image.paste(noimage, (0, int((height - width) / 2)), noimage)

        image = self.process_image(image)
        image = discord.File(fp=image, filename='noemote.png')
        await ctx.send(file=image)

    @emote.command()
    @commands.bot_has_permissions(manage_emojis=True)
    @checks.check_permissions_or_owner(manage_emojis=True)
    async def add(self, ctx, emoji_name: str, url=None):
        """Adds an emoji to the guild.
        
        You must have Manage Emojis permission to use this."""
        if not url:
            if ctx.message.attachments:
                emoji_aio = await self.aiosessionget(ctx.message.attachments[0].url)
            else:
                return await ctx.send("❌ You need to provide a url or have an attachment on your message!\n"
                                      f"Please see `{ctx.prefix}{ctx.command}` for more info.")
        else:
            try:
                emoji_aio = await self.aiosessionget(url)
            except ValueError:
                return await ctx.send("❌ You need to provide a url or have an attachment on your message!\n"
                                      f"Please see `{ctx.prefix}{ctx.command}` for more info.")

        try:
            finalized_e = await ctx.guild.create_custom_emoji(name=emoji_name, image=emoji_aio, 
                                                              reason=f"Emoji Added by {ctx.author} "
                                                              f"(ID: {ctx.author.id})")
        except Exception as ex:
            print(ex)
            return await ctx.send("Something went wrong creating that emoji. Make sure this guild"
                                  " emoji\'s list isn\'t full and that emoji is under 256kb.")
        await ctx.send(f"Successfully created {finalized_e} -- `{finalized_e}`")

    @emote.command()
    @commands.bot_has_permissions(manage_emojis=True)
    @checks.check_permissions_or_owner(manage_emojis=True)
    async def delete(self, ctx, emote: discord.Emoji):
        """Deletes an emoji from the guild.
        
        You must have Manage Emojis permission to use this.

        This is a case-sensitive command."""
        if ctx.guild.id == emote.guild.id:
            await emote.delete(reason=f"Emoji Removed by {ctx.author} (ID: {ctx.author.id})")
            await ctx.send("Emote is now deleted.")
        else:
            return await ctx.send("That emote is not in this guild. "
                                  "Run this command again in the guild that has that emote")

    @add.error
    @delete.error
    async def emoji_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'{ctx.author.mention}: You gave incorrect arguments.')
            return await ctx.send_help(ctx.command)
        elif isinstance(error, commands.BotMissingPermissions):
            rn = '\n-'.join(error.missing_perms)
            return await ctx.send("Bot is missing permissions. Please add the following permissions\n"
                                  f"```- {rn}```")
        elif isinstance(error, commands.CheckFailure):
            return await ctx.send(f"{ctx.author.mention}: You don't have the required "
                                  "permissions to use this command.")
        elif isinstance(error, commands.BadArgument):
            return await ctx.send("Emoji not found.")

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        try:
            # Search for emoji-list in the guild
            emoji_chan = discord.utils.get(guild.channels, name='emoji-list')
            rm_emoji = [f"{emoji}" for emoji in before if emoji not in after]
            mk_emoji = [f"{emoji} `:{emoji.name}:`" for emoji in after if emoji not in before]
            # Prepare Message
            if len(rm_emoji) != 0:
                msg = "⚠ Emoji Removed: "
                msg += ", ".join(rm_emoji)
                await emoji_chan.send(msg)
            if len(mk_emoji) != 0:
                msg = "✅ Emoji Added: "
                msg += ", ".join(mk_emoji)
                await emoji_chan.send(msg)
        except:
            # Handle botaww not being able to talk in the channel
            pass

def setup(bot):
    bot.add_cog(Emote(bot))