import asyncio
import datetime
import aiohttp
from prometheus_client import CollectorRegistry
from collections import deque, defaultdict

from discord.ext.commands import AutoShardedBot

from Bot import Handlers
from Utils import Utils





class AutoMod(AutoShardedBot):
    """
    A subclass of AutoShardedBot
    The handling of initial events 
    through the Handlers.py file
    is inspired by GearBot
    (https://github.com/gearbot/GearBot)
    """
    READY = False
    version = ""
    command_count = 0
    custom_command_count = 0
    locked = True
    shard_count = 1
    shard_ids = []
    missing_guilds = []
    loading_task = None
    initial_fill_complete = False
    aiosession = None
    errors = 0
    own_messages = 0
    bot_messages = 0
    user_messages = 0
    cleans_running = dict()
    running_unbans = set()
    running_msg_deletions = set()
    running_removals = set()
    metrics_registry = CollectorRegistry()
    last_reload = None
    
    
    def __init__(self, *args, loop=None, **kwargs):
        super().__init__(*args, loop=loop, **kwargs)
        self.total_shards = kwargs.get("shard_count", 1)

        self.session = aiohttp.ClientSession(loop=self.loop)
        self.prev_events = deque(maxlen=10)

        self.resumes = defaultdict(list)
        self.identifies = defaultdict(list)


    def _clear_gateway_data(self):
        ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        for sid, dates in self.identifies.items():
            needs_removal = [i for i, dt in enumerate(dates) if dt < ago]
            for i in reversed(needs_removal):
                del dates[i]

        for sid, dates in self.resumes.items():
            needs_removal = [i for i, dt in enumerate(dates) if dt < ago]
            for i in reversed(needs_removal):
                del dates[i]

    async def _run_event(self, coro, event_name, *args, **kwargs):
        while (self.locked or not self.READY) and event_name != "on_ready":
            await asyncio.sleep(0.2)
        await super()._run_event(coro, event_name, *args, **kwargs)


    async def on_socket_response(self, message):
        self.prev_events.append(message)


    async def on_shard_resumed(self, sid):
        self.resumes[sid].append(datetime.datetime.utcnow())
    

    async def before_identify_hook(self, sid, *, initial):
        self._clear_gateway_data()
        self.identifies[sid].append(datetime.datetime.utcnow())
        await super().before_identify_hook(sid, initial=initial)
        


    def run(self): # a custom run function
        try:
            super().run(Utils.from_config("TOKEN"), reconnect=True)
        finally:
            with open("prev_events.log", "w", encoding="utf-8") as f:
                for data in self.prev_events:
                    try:
                        x = json.dumps(data, ensure_ascii=True, indent=4)
                    except:
                        f.write(f"{data}\n")
                    else:
                        f.write(f"{x}\n")
    
    """Events handled through Handlers.py"""
    async def on_ready(self):
        await Handlers.on_ready(self)

    async def on_message(self, message):
        await Handlers.on_message(self, message)

    async def on_guild_join(self, guild):
        await Handlers.on_guild_join(self, guild)

    async def on_guild_remove(self, guild):
        await Handlers.on_guild_remove(self, guild)

    async def on_command_error(self, ctx, error):
        await Handlers.on_command_error(self, ctx, error)

    async def on_guild_update(self, before, after):
        await Handlers.on_guild_update(before, after)

    async def on_shard_connect(self, shard_id):
        await Handlers.on_shard_connect(self, shard_id)

    async def on_shard_disconnect(self, shard_id):
        await Handlers.on_shard_disconnect(self, shard_id)
    
    async def on_shard_ready(self, shard_id):
        await Handlers.on_shard_ready(self, shard_id)

    async def on_shard_resumed(self, shard_id):
        await Handlers.on_shard_resumed(self, shard_id)