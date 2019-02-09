from discord.ext import commands
import discord
import os
import io
import math
from PIL import Image

class Emote:
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
    
    @commands.group()
    async def emote(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('You need to specify an emotetype.')

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
     
def setup(bot):
    bot.add_cog(Emote(bot))
