import time
from openai import AsyncOpenAI

import chainlit as cl
import json

# Load the API URL from the config file
api_url =''

with open('app.config', 'r') as config_file:
    config = json.load(config_file)
    api_url = config.get("apiUrl", "http://default-url.com")


client = AsyncOpenAI(
    api_key="ollama",
    base_url= api_url
    )

settings = {
    "model": "R1-Qwen-32B-Int4-W4A16",
    "temperature": 0.6,
    # ... more settings
}

@cl.on_message
async def on_message(msg: cl.Message):
    start = time.time()
    stream = await client.chat.completions.create(
        #model="R1-Qwen-32B-Int4-W4A16",
        **settings,
        messages=[
            {"role": "user", "content": "You are an helpful assistant"},
            *cl.chat_context.to_openai()
        ],
        stream=True
    )

    thinking = False
    
    # Streaming the thinking
    async with cl.Step(name="Thinking") as thinking_step:
        final_answer = cl.Message(content="")

        async for chunk in stream:
            delta = chunk.choices[0].delta

            if delta.content == "<think>":
                thinking = True
                continue
                
            if delta.content == "</think>":
                thinking = False
                thought_for = round(time.time() - start)
                thinking_step.name = f"Thought for {thought_for}s"
                await thinking_step.update()
                continue
            
            if thinking:
                await thinking_step.stream_token(delta.content)
            else:
                await final_answer.stream_token(delta.content)
                
    await final_answer.send()