import asyncio

import discord
from celery.exceptions import TaskRevokedError

from apps.youtube_summarizer import YoutubeSummarizer
from helpers import add_async_command, await_task, TaskFailedError
from celeryconf import celery_app


# Split text into less than 2000 characters to avoid Discord's 2000 character limit
def split_text(text, max_len=1990):
    if len(text) <= max_len:
        return [text]

    parts = []
    while len(text) > max_len:
        split_index = max_len
        while text[split_index] != ' ' and split_index > 0:
            split_index -= 1

        if split_index == 0:
            raise ValueError("No whitespace found to split the text.")

        parts.append(text[:split_index])
        text = text[split_index:].strip()

    parts.append(text)
    return parts


@celery_app.task
def youtube_summarizer_task(url: str):
    summarizer = YoutubeSummarizer(url, debug=True)
    output = summarizer.get_youtube_summary()
    return output


@add_async_command
async def youtube(ctx, url: str):
    """
    Given a YouTube url, the model will return a summary of the video.
    """
    formatted_output = f'''
**[Youtube Summarizer]**
{ctx.author.mention}
> /youtube url:{url}
'''
    # For some reason if you call ctx.defer() before sending a message you can't create a thread.
    # So let's send a message first, then edit it later
    message = await ctx.send(formatted_output + '```Loading...```')
    try:
        output = await await_task(youtube_summarizer_task.delay(url))
    except TaskRevokedError:
        await ctx.send('Task timed out')
        return
    except TaskFailedError:
        await ctx.send('Task failed')
        return

    if output.get('reduction'):
        print('reduction')
        formatted_output += f'```{output["reduction"]}```\n'
        print(f'{len(formatted_output) = }')
        await message.edit(content=formatted_output)
        thread = await message.create_thread(name='Summary')
        print('thread')
        for part in split_text(output['summary']):
            await thread.send(f'```{part}```')
    else:
        print('no reduction')
        await ctx.send(f'{formatted_output}\n```{output["summary"]}```')


@add_async_command
async def start_thread(ctx, name: str):
    """Start a new thread in the current text channel."""
    message = await ctx.send(f"Waiting a bit to start thread '{name}'...")
    await asyncio.sleep(5)
    await message.edit(content=f"Starting thread '{name}'...")
    thread = await message.create_thread(name=name)
    await thread.send(f"A new thread named '{name}' has been created!")
