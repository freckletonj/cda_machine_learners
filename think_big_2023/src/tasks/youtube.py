from apps.youtube_summarizer import YoutubeSummarizer
from helpers import add_async_command, process_deferred_task
from celeryconf import celery_app


@celery_app.task
def youtube_summarizer_task(url: str):
    summarizer = YoutubeSummarizer(url)
    output = summarizer.summarize()
    formatted_output = f'**Youtube Summarizer**\n\nURL:\n> {url}\n\nOutput:\n```\n{output}\n```'
    return formatted_output


@add_async_command
async def youtube_summarizer(ctx, url: str):
    """
    Given a youtube url, the model will return a summary of the video.
    """
    await process_deferred_task(ctx, youtube_summarizer_task.delay(url))
