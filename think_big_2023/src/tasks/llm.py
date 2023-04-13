import discord
from apps import our_openai as openai
from helpers import add_async_command, process_deferred_task
from celeryconf import celery_app
from transformers import pipeline


# Sentiment Analysis

@celery_app.task
def sentiment_analysis_task(prompt: str):
    model = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')
    return f'`[Text Classification]` {model(prompt)}'


@add_async_command
@discord.ext.commands.guild_only()
async def sentiment_analysis(ctx, prompt: str):
    """
    Given text, the model will return a polarity (positive, negative,
    neutral) or a sentiment (happiness, anger).

    task: https://huggingface.co/tasks/text-classification
    model: distilbert-base-uncased-finetuned-sst-2-english
    size: 268 MB
    dataset: https://huggingface.co/datasets/sst2
    source: https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english
    """
    await process_deferred_task(ctx, sentiment_analysis_task.delay(prompt))


# Text Generation

@celery_app.task
def text_generation_task(prompt: str):
    model = pipeline('text-generation', model='gpt2')
    return f'`[Text Generation]` {model(prompt)}'


@add_async_command
@discord.ext.commands.guild_only()
async def text_generation(ctx, prompt: str):
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
    await process_deferred_task(ctx, text_generation_task.delay(prompt))


# ChatGPT4

@celery_app.task
def gpt4_chat_task(prompt: str):
    completion = openai.ChatCompletion.create(
        model='gpt-4',
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
    return f'`[Conversation GPT4]` {completion.choices[0].message}'


@add_async_command
@discord.ext.commands.guild_only()
async def gpt4_chat(ctx, prompt: str):
    """
    Given a chat conversation, the model will return a chat completion response.

    task: https://huggingface.co/tasks/conversational
    model: chatgpt4
    size: unknown
    dataset: unknown
    source: closed
    """
    await process_deferred_task(ctx, gpt4_chat_task.delay(prompt))
