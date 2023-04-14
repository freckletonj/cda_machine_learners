import discord
from celery.exceptions import TaskRevokedError

from apps import our_openai as openai
from helpers import add_async_command, process_deferred_task, await_task, TaskFailedError
from celeryconf import celery_app
from transformers import pipeline


# Sentiment Analysis

@celery_app.task
def sentiment_analysis_task(prompt: str):
    model = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
    return model(prompt)
    formatted_output = f'**Sentiment Analysis**\n\nPrompt:\n> {prompt}\n\nLabel: **{output[0]["label"]}**\nScore: **{output[0]["score"]}**'

    return formatted_output


@add_async_command
@discord.ext.commands.guild_only()
async def sentiment(ctx, prompt: str):
    """
    Given text, the model will return a polarity (positive, negative,
    neutral) or a sentiment (happiness, anger).

    task: https://huggingface.co/tasks/text-classification
    model: distilbert-base-uncased-finetuned-sst-2-english
    size: 268 MB
    dataset: https://huggingface.co/datasets/sst2
    source: https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english
    """
    await ctx.defer()
    try:
        result = await await_task(sentiment_analysis_task.delay(prompt))
    except TaskRevokedError:
        await ctx.send('Task timed out')
        return
    except TaskFailedError:
        await ctx.send('Task failed')
        return
    formatted_response = f'''
**`[Sentiment Analysis]`** 
{ctx.author.mention}
> /sentiment prompt:{prompt}
*Prediction:* {result['label']}
*Confidence:* {result['score']:>0.4f}
'''

    await ctx.send(formatted_response)


# Text Generation

@celery_app.task
def text_generation_task(prompt: str):
    model = pipeline('text-generation', model='gpt2')
    output = model(prompt)
    return output[0]['generated_text']


@add_async_command
@discord.ext.commands.guild_only()
async def continuation(ctx, prompt: str):
    """
    Given text, the model will return generated text.

    task: https://huggingface.co/tasks/text-generation
    model: gpt2
    size: 548 MB
    dataset:
        - https://github.com/openai/gpt-2/blob/master/domains.txt
        - https://huggingface.co/datasets/openwebtext
    source: https://huggingface.co/gpt2
    """
    await ctx.defer()
    try:
        result = await await_task(text_generation_task.delay(prompt))
    except TaskRevokedError:
        await ctx.send('Task timed out')
        return
    except TaskFailedError:
        await ctx.send('Task failed')
        return
    formatted_response = f'''
**`[Text Continuation]`** 
{ctx.author.mention}
> /continuation prompt: {prompt} 
{result}
'''
    await ctx.send(formatted_response)


# ChatGPT4

@celery_app.task
def chat_task(prompt: str):
    """Chat with a robot. Ask it for a poem, or historical fact, or a joke!"""
    completion = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            # The system message helps set the behavior of the assistant
            {'role': 'system', 'content': 'You are a very knowledgable entity.'},
            # The user messages help instruct the assistant
            {'role': 'user', 'content': prompt},
            # The assistant messages help store prior responses
            # (provides context or desired behavior)
            # {'role': 'assistant', 'content': 'TODO!'},
        ],
    )
    return str(completion.choices[0].message)


@add_async_command
@discord.ext.commands.guild_only()
async def chat(ctx, prompt: str):
    """
    Given a chat conversation, the model will return a chat completion response.
    """
    # Even though this is a simple API call, openai can't be awaited and will block the main thread.
    # So we defer the task to a celery worker.
    await ctx.defer()
    try:
        result = await await_task(chat_task.delay(prompt))
    except TaskRevokedError:
        await ctx.send('Task timed out')
        return
    except TaskFailedError:
        await ctx.send('Task failed')
        return

    out = f'''
**`[ChatGPT]`** 
{ctx.author.mention}
> /chat prompt: {prompt}

*Q:* {prompt}
*A:* {result}
'''
    await ctx.send(out)