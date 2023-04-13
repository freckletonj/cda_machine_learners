import asyncio
import inspect
import sys
from functools import wraps

from bot import bot


def export(func):
    """Use a snippit to avoid retyping function/class names."""
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
    await ctx.defer()
    i = 0
    while not task.ready():
        await asyncio.sleep(1)
        i += interval
        if i > 900:
            task.revoke()
            await ctx.send('Task took too long')
            print('Task took too long')
            return
    await ctx.send(task.get())
