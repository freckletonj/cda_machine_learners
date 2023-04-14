import asyncio

import discord

from celeryconf import celery_app
from helpers import add_async_command, process_deferred_task
from session import get_session
import io
import base64

url = "http://127.0.0.1:7860"


# Stable Diffusion


@celery_app.task
async def image_task(prompt: str):
    payload = {
        "prompt": prompt,
        "steps": 40,

        "width": 512,
        "height": 512,
        # "firstpass_width": 512,
        # "firstpass_height": 512,

        "negative_prompt": "blurry",
    }

    async with get_session().post(url=f'{url}/sdapi/v1/txt2img', json=payload) as response:
        r = await response.json()

        for i in r['images']:
            image = io.BytesIO(base64.b64decode(i.split(",", 1)[0]))
            return image


@add_async_command
@discord.ext.commands.guild_only()  # don't respond on DMs
async def image(ctx, prompt: str):
    await ctx.defer()
    try:
        task = image_task.delay(prompt)
        i = 0
        while not task.ready():
            await asyncio.sleep(1)
            i += 1
            if i > 900:
                await ctx.reply(f"Image generation timed out after 15 minutes")
                return
        base64_image = task.get()
        file = discord.File(base64_image, 'image.png')
        content = f'**Stable Diffusion Image**\n\nPrompt:\n> {prompt}'
        await ctx.reply(file=file, content=txt)
    except Exception as e:
        await ctx.reply(f"Image generation failed")
