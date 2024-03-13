import asyncio
import socketio
#import uvicorn
from aiohttp import web
#from transformers import pipeline
from modules.AiAgent import *
import json
from modules import DocumentReader
import io


# create a Socket.IO server
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
# wrap with a WSGI application
app = web.Application()

sio.attach(app)
#app = socketio.ASGIApp(sio)

#uvicorn.run(app, host='localhost', port=5000)

class MessageRecipients:
    GENERATOR = 1
    SUGGESTER = 2
    SUMMARIZER = 3
    AGENT_SELECTOR = 4

global agent

agent = AI_AGENT_LLAMA_CPP("TheBloke/phi-2-GGUF", "phi-2.Q4_K_M.gguf")
#agent = AI_AGENT_LLAMA_CPP("TheBloke/stablelm-zephyr-3b-GGUF", "stablelm-zephyr-3b.Q4_K_M.gguf")
#agent = AI_AGENT_LLAMA_CPP("TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
#agent = AI_AGENT_TRANSFORMER('gpt2')#"TinyLlama/TinyLlama-1.1B-Chat-v1.0")
#pipe = pipeline("text-generation", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", num_workers=12)#"gpt2")
"""
async def stream_data(websocket, initial_text):
    # Define the function you want to execute when a message is received
    for i in range (10):
        gen = pipe(initial_text, max_length=len(pipe.tokenizer.encode(initial_text)) + 1, return_full_text=False)
        initial_text += " " + gen[0]['generated_text']
        await websocket.send(gen[0]['generated_text'])
        print(f"Streamed Sent message: {gen[0]['generated_text']}")
    return initial_text
"""

async def change_agent(sid, new_agent_repo, new_agent_name):
    global agent
    agent = AI_AGENT_LLAMA_CPP(new_agent_repo, new_agent_name)
    print(f"Changed to agent: {new_agent_name}/{new_agent_repo}")
    data = json.dumps({"status":"successful", "from_generator": False, "from_suggester": False, "from_agent_change":True})
    await sio.emit("message", data)

async def generate(message, Generation_count = 10):
    # Define the function you want to execute when a message is received
    print(f"Received generation request for message: '''{message}'''")
    for i in range (Generation_count):
        #gen = pipe(message, max_length=len(pipe.tokenizer.encode(message)) + 1, num_return_sequences=1, return_full_text=False, do_sample=True)#, prefix="An Example of a Ai Generated Text:\n")
        gen, break_model_signal = agent.generate_response(message, return_full_text=False)
        gen = gen[0]
        print(gen)
        #message += gen[0]['generated_text']
        message += gen
        data = json.dumps({"message": gen, "from_generator": True, "from_suggester": False, "from_agent_change":False})
        await sio.emit("message", data)
        await asyncio.sleep(0.01)
        print(f"Streamed Sent message: '''{gen}'''")#[0]['generated_text']}")
        if break_model_signal:
            break
        
    print(f"Sent message: '''{message}'''")

async def suggest(message, num_return_sequences):
    print(f"Received suggestion request for message: '''{message}'''")
    #gen = pipe(message, max_length=len(pipe.tokenizer.encode(message)) + 1, num_return_sequences=num_return_sequences, return_full_text=False, do_sample=True)
    gen, break_model_signal = agent.generate_response(message, num_return_sequences=num_return_sequences, return_full_text=False)
    print(gen)
    gen = list(set(gen)) #get unique values
    data = json.dumps({"message": gen, "from_generator": False, "from_suggester": True, "from_agent_change":False})
    await sio.emit("message", data)
    await asyncio.sleep(0.01)
    print(f"Sent message: '''{data}'''")

async def summarizer(binary_file, type):
    file = DocumentReader.Reader(io.BytesIO(binary_file), type)
    text = file.get_text() + "\n\nThe summary of the content is:"
    await generate(text, Generation_count = 100)

@sio.on('message')
async def websocket_handler(sid, data):
    #print(str(data))

    json_obj = data
    print(f"Received message of type {type(data)}, from {sid}, for recipient id {json_obj['recipient']}")

    if json_obj['recipient'] == MessageRecipients.GENERATOR:
        await generate(json_obj['message'], json_obj['generation_count'])
    if json_obj['recipient'] == MessageRecipients.SUGGESTER:
        await suggest(json_obj['message'], json_obj['no_of_samples'])
    if json_obj['recipient'] == MessageRecipients.SUMMARIZER:
        await summarizer(json_obj['file'], json_obj['type'])
    if json_obj['recipient'] == MessageRecipients.AGENT_SELECTOR:
        await change_agent(sid, json_obj['model_repo'], json_obj['model_name'])

                

@sio.event
async def connect(sid, environ,  auth):
    print("Client connected")
    print(f"Client connected: {sid}\nEnvironment: {environ}\nAuth: {auth}")

@sio.event
async def disconnect(sid):
    print("Client disconnected")
    print(f"Client disconnected: {sid}")

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)
    print("Server running on port 5000")