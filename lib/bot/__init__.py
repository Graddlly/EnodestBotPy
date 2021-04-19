from discord.ext.commands import Bot as BotBase
from discord.ext.commands import CommandNotFound

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..db import db

PREFIX = '>'
OWNER_IDS = []

class BotS(BotBase):
    def __init__(self):
        super().__init__(command_prefix = PREFIX, owner_ids = OWNER_IDS)

        self.ready = False
        self.guild = None
        self.scheduler = AsyncIOScheduler()

        db.autosave(self.scheduler)

        super().__init__(command_prefix = PREFIX, owner_ids = OWNER_IDS)

    def run(self, version):
        self.VERSION = version

        with open('./lib/bot/token', mode = 'r', encoding = 'utf-8') as tokenfile:
            self.TOKEN = tokenfile.read()

        print('[EnodestBot] Running...')
        super().run(self.TOKEN, reconnect = True)

    async def on_connect(self):
        print('[EnodestBot] Connected')

    async def on_disconnect(self):
        print('[EnodestBot] Disconnected')

    async def on_error(self, err, *args, **kwargs):
        if err == 'on_command_error':
            await args[0].send('[EnodestBot] Something went wrong...')

        print('[EnodestBot] An error occured')
        raise

    async def on_command_error(self, ctx, exc):
        if not isinstance(exc, CommandNotFound):
            raise exc.original

    async def on_ready(self):
        if not self.ready:
            self.ready = True
            self.scheduler.start()
            print('[EnodestBot] Ready')
        else:
            print('[EnodestBot] Reconnecting...')

    async def on_message(self, message):
        pass

bot = BotS()