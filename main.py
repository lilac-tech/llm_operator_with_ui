import asyncio
import websockets
#from transformers import pipeline
from modules.AiAgent import *
import json
from modules import DocumentReader

class MessageRecipients:
    GENERATOR = 1
    SUGGESTER = 2
    SUMMARIZER = 3

global chunks

agent = None #AI_AGENT_LLAMA_CPP("TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
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

async def change_agent(websocket, new_agent_name):
    global agent
    agent = AI_AGENT_LLAMA_CPP(new_agent_name)
    print(f"Changed to agent: {new_agent_name}")

async def generate(websocket, message, Generation_count = 10):
    # Define the function you want to execute when a message is received
    print(f"Received generation request for message: '''{message}'''")
    for i in range (Generation_count):
        #gen = pipe(message, max_length=len(pipe.tokenizer.encode(message)) + 1, num_return_sequences=1, return_full_text=False, do_sample=True)#, prefix="An Example of a Ai Generated Text:\n")
        gen, break_model_signal = agent.generate_response(message, return_full_text=False)
        gen = gen[0]
        print(gen)
        #message += gen[0]['generated_text']
        message += gen
        data = json.dumps({"message": gen, "from_generator": True, "from_suggester": False})
        await websocket.send(data)
        await asyncio.sleep(0.0)
        print(f"Streamed Sent message: '''{gen}'''")#[0]['generated_text']}")
        if break_model_signal:
            break
        
    print(f"Sent message: '''{message}'''")

async def suggest(websocket, message, num_return_sequences):
    print(f"Received suggestion request for message: '''{message}'''")
    #gen = pipe(message, max_length=len(pipe.tokenizer.encode(message)) + 1, num_return_sequences=num_return_sequences, return_full_text=False, do_sample=True)
    gen, break_model_signal = agent.generate_response(message, num_return_sequences=num_return_sequences, return_full_text=False)
    print(gen)
    gen = list(set(gen)) #get unique values
    data = json.dumps({"message": gen, "from_generator": False, "from_suggester": True})
    await websocket.send(data)
    await asyncio.sleep(0.0)
    print(f"Sent message: '''{data}'''")


async def websocket_handler(websocket, path):
    # This function will be called whenever a new connection is established
    print(f"WebSocket connection established: {websocket.remote_address}")
    while True:
        try:
            data = await websocket.recv()

            print(str(data))

            json_obj = json.loads(data)
            print(f"Received message of type {type(data)}, from {websocket.remote_address}, for {json_obj['recipient']}")

            if json_obj['recipient'] == MessageRecipients.GENERATOR:
                await generate(websocket, json_obj['message'], json_obj['generation_count'])
            if json_obj['recipient'] == MessageRecipients.SUGGESTER:
                await suggest(websocket, json_obj['message'], json_obj['no_of_samples'])
            if json_obj['recipient'] == MessageRecipients.SUMMARIZER:
                a = DocumentReader.DocxReader(json_obj['file'])
                a = a.get_text()
                print(a)
                
            
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
            break

if __name__ == "__main__":
    print("Hello, World!")
    # Define your WebSocket server information
    host = "localhost"
    port = 8000 #8765

    # Start the WebSocket server
    start_server = websockets.serve(websocket_handler, host, port)

    print(f"WebSocket server started at ws://{host}:{port}")

    # Run the event loop to keep the server running
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
