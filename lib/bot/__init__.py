from discord.ext.commands import Bot as BotBase
from discord.ext.commands import (CommandNotFound, BadArgument, MissingRequiredArgument, CommandOnCooldown)
from discord.ext.commands import Context
from discord.ext.commands import when_mentioned_or, command, has_permissions

from discord.errors import HTTPException, Forbidden

from discord import Embed, File, DMChannel

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from glob import glob
from asyncio import sleep
from datetime import datetime

import os
from pathlib import Path
from dotenv import load_dotenv
env_path = Path('.')/'.env'
load_dotenv(dotenv_path = env_path)

OWNER_IDS = [169455756381388800]
IGNORE_EXCEPTIONS = (CommandNotFound, BadArgument)
COGS = [path.split("\\")[-1][11:-3] for path in glob("./lib/cogs/*.py")]

class BotReady(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f"[EnodestBot] {cog} cog ready")

    def all_ready(self):
        return all(getattr(self, cog) for cog in COGS)

class BotS(BotBase):
    def __init__(self):
        self.ready = False
        self.guild = None
        self.cogs_ready = BotReady()
        self.scheduler = AsyncIOScheduler()

        try:
            with open('./data/banlist.txt', mode = 'r', encoding = 'utf-8') as bl:
                self.banlist = [int(line.strip()) for line in bl.readlines()]
        except FileNotFoundError:
            self.banlist = []

        super().__init__(command_prefix = '>', owner_ids = OWNER_IDS)

    def setup(self):
        for cog in COGS:
            self.load_extension(f'lib.cogs.{cog}')
            print(f"[EnodestBot] {cog} cog loaded")

        print('[EnodestBot] Setup: initializing cogs complete')

    def run(self, version):
        self.VERSION = version

        print('[EnodestBot] Setup: running')
        self.setup()

        self.TOKEN = os.getenv('TOKEN')

        print('[EnodestBot] Running...')
        super().run(self.TOKEN, reconnect = True)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls = Context)

        if ctx.command is not None and ctx.guild is not None:
            if message.author.id in self.banlist:
                await ctx.send("You`re banned for this.")
            elif not self.ready:
                await ctx.send("Bot not ready to receive command. Please, wait a few minutes.")
            else:
                await self.invoke(ctx)

    async def on_connect(self):
        print('[EnodestBot] Connected')

    async def on_disconnect(self):
        print('[EnodestBot] Disconnected')

    async def on_error(self, err, *args, **kwargs):
        if err == 'on_command_error':
            await args[0].send('Something went wrong...')

        print('[EnodestBot] An error occured')
        raise

    async def on_command_error(self, ctx, exc):
        if any(isinstance(exc, error) for error in IGNORE_EXCEPTIONS):
            pass
        elif isinstance(exc, MissingRequiredArgument):
            await ctx.send('One or more requirements (arguments) are missing.')
        elif isinstance(exc, CommandOnCooldown):
            await ctx.send(f"That command is on {str(exc.cooldown.type).split('.')[-1]} cooldown. Try again in {exc.retry_after:,.2f} secs.")
        elif hasattr(exc, 'original'):
            if isinstance(exc.original, Forbidden):
                await ctx.send("I do not have permission to do that.")
            else:
                raise exc.original
        else:
            raise exc

    async def on_ready(self):
        if not self.ready:
            self.guild = self.get_guild(os.getenv('GUILD'))
            self.log_channel = self.get_channel(os.getenv('LOG_CHANNEL'))

            while not self.cogs_ready.all_ready():
                await sleep(0.5)

            self.ready = True
            print('[EnodestBot] Ready')

            meta = self.get_cog('meta')
            await meta.set()
        else:
            print('[EnodestBot] Reconnecting...')

    async def on_message(self, message):
        if not message.author.bot and isinstance(message.channel, DMChannel):
            if len(message.content) < 50:
                await message.channel.send('Your message should be at least 50 characters in length.')
            else:
                member = self.guild.get_member(message.author.id)
                embed = Embed(
                    title = 'Moderation Mail',
                    colour = member.colour,
                    timestamp = datetime.utcnow()
                )

                embed.set_thumbnail(url = member.avatar.url)

                fields = [('Member', member.display_name, False), ('Message', message.content, False)]
                for name, value, inline in fields:
                    embed.add_field(name = name, value = value, inline = inline)
                
                mod = self.get_cog('moderation')
                await mod.log_channel.send(embed = embed)
                await message.channel.send('Message relayed to moderators.')
        else:
            await self.process_commands(message)

bot = BotS()