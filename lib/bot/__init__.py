from discord.ext.commands import Bot as BotBase
from discord.ext.commands import CommandNotFound

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from glob import glob

from ..db import db

PREFIX = '>'
OWNER_IDS = []
COGS = [path.split('\\')[-1][:-3] for path in glob('./lib/cogs/*.py')]

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
        super().__init__(command_prefix = PREFIX, owner_ids = OWNER_IDS)

        self.PREFIX = PREFIX
        self.ready = False
        self.guild = None
        self.cogs_ready = BotReady()
        self.scheduler = AsyncIOScheduler()

        db.autosave(self.scheduler)

        super().__init__(command_prefix = PREFIX, owner_ids = OWNER_IDS)

    def setup(self):
        for cog in COGS:
            self.load_extension(f"lib.cogs.{cog}")
            print(f"[EnodestBot] {cog} cog loaded")

        print('[EnodestBot] Setup: initializing cogs complete')

    def run(self, version):
        self.VERSION = version

        print('[EnodestBot] Setup: running')
        self.setup()

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
            self.scheduler.start()
            self.ready = True

            while not self.cogs_ready.all_ready():
                await sleep(0.5)

            print('[EnodestBot] Ready')
        else:
            print('[EnodestBot] Reconnecting...')

    async def on_message(self, message):
        pass

bot = BotS()