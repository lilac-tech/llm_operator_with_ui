from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

class AI_AGENT_TRANSFORMER:
    def __init__(self, model_name):
        self.model = self.initialize_model(model_name)
        self.tokenizer = self.initialize_tokenizer(model_name)

    def initialize_model(self, model_name: str):
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        return model
        
    def initialize_tokenizer(self, model_name: str):
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        tokenizer.bos_token_id = 1  # Set beginning of sentence token id
        return tokenizer

    def generate_response(self, prompt, max_new_tokens=1, num_return_sequences=1, return_full_text=True, do_sample=True, sampling_top_k=50):
        inputs = self.tokenizer.encode(
            prompt,
            return_tensors='pt'
        )
        #parameter doc at https://huggingface.co/docs/transformers/en/main_classes/text_generation#transformers.GenerationConfig
        tokens = self.model.generate(
            inputs.to(self.model.device),
            max_new_tokens=max_new_tokens,
            num_return_sequences=num_return_sequences,
            temperature=0.5,
            do_sample=do_sample,
            top_k=sampling_top_k
        )
        if not return_full_text:
            lens = list(map(lambda x: len(x), inputs))
            tokens = list(map(lambda x: x[lens[0]:], tokens))
        res = list(map(lambda x: self.tokenizer.decode(x, skip_special_tokens=True), tokens))

        break_model_signal = False
        if not return_full_text and max_new_tokens != 1 and res[0] == "":
            break_model_signal = True
            
        return res, break_model_signal
    
class AI_AGENT_LLAMA_CPP:
    def __init__(self, model_name, filename):
        self.model = self.initialize_model(model_name, filename)
    
    def initialize_model(self, model_name, filename):
        model_path = hf_hub_download(model_name, filename=filename)
        model = Llama(
            model_path=model_path,
            n_ctx=1024*8,
            n_threads=12,
            n_gpu_layers=0,
            use_mmap=True,
            n_batch=512,
            mul_mat_q=True,
            numa=True,
        )
        return model
    
    def generate_response(self, prompt, max_new_tokens=1, num_return_sequences=1, return_full_text=True, do_sample=True, sampling_top_k=10):
        ## Generation kwargs
        #more info at https://llama-cpp-python.readthedocs.io/en/latest/api-reference/#llama_cpp.Llama.__call__
        generation_kwargs = {
            "max_tokens":max_new_tokens,
            "stop":["</s>"],
            "echo":return_full_text, # Echo the prompt in the output
            "top_k":sampling_top_k if do_sample else 1, # This is essentially greedy decoding, since the model will always return the highest-probability token. Set this value > 1 for sampling decoding
        }

        ## Generate
        gen = []
        for _ in range(num_return_sequences): 
            gen.append(
                self.model(
                    prompt,
                    **generation_kwargs
                )
            )

        print(gen)
        
        break_model_signal = False
        if not return_full_text and max_new_tokens != 1 and gen[0]["choices"][0]['finish_reason']=="stop":
            break_model_signal = True
            
        ## Return
        gen = list(map(lambda x: x["choices"][0]["text"], gen))
        return gen, break_model_signal


"""
## Imports

## Download the GGUF model
model_name = "TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF"
model_file = "mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf" # this is the specific model file we'll use in this example. It's a 4-bit quant, but other levels of quantization are available in the model repo if preferred
model_path = hf_hub_download(model_name, filename=model_file)

## Instantiate model from downloaded file
llm = Llama(
    model_path=model_path,
    n_ctx=16000,  # Context length to use
    n_threads=32,            # Number of CPU threads to use
    n_gpu_layers=0        # Number of model layers to offload to GPU
)

## Generation kwargs
generation_kwargs = {
    "max_tokens":20000,
    "stop":["</s>"],
    "echo":False, # Echo the prompt in the output
    "top_k":1 # This is essentially greedy decoding, since the model will always return the highest-probability token. Set this value > 1 for sampling decoding
}

## Run inference
prompt = "The meaning of life is "
res = llm(prompt, **generation_kwargs) # Res is a dictionary

## Unpack and the generated text from the LLM response dictionary and print it
print(response["choices"][0]["text"])
"""