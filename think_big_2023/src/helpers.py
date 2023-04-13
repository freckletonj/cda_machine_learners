import asyncio
import sys
from bot import bot
import aiohttp

_session = None


def get_session():
    global _session
    if _session is None:
        _session = aiohttp.ClientSession()
    return _session


def close_session():
    global _session
    if _session is not None:
        _session.close()
        _session = None


def export(func):
    """
    Use a snippit to avoid retyping function/class names.
    Automatically adds the function to the module's __all__ list.
    This allows the function to be imported with `from module import *`.
    """
    mod = sys.modules[func.__module__]
    if hasattr(mod, '__all__'):
        name = func.__name__
        all_ = mod.__all__
        if name not in all_:
            all_.append(name)
    else:
        mod.__all__ = [func.__name__]


def add_async_command(func):
    """Decorator to add a synchronous command to the Discord bot and export it to the module."""
    export(func)
    decorated_func = bot.hybrid_command()(func)
    return decorated_func


async def process_deferred_task(ctx, task, interval=3):
    """Automatically handle simple deferred tasks."""
    await ctx.defer()
    i = 0
    while not task.ready():
        await asyncio.sleep(interval)
        i += interval
        if i > 900:
            task.revoke()
            await ctx.send('Task took too long')
            print('Task took too long')
            return
    await ctx.send(task.get())
