# ollama run qwen2.5-coder:1.5b
# model: -> aikid123/Qwen3-coder
import ollama;

#create a ollama obj
my_lama = ollama.Client()

model = "aikid123/Qwen3-coder:1.7b"
prompt = "What is prisoners delima?"

response = my_lama.generate(model = model, prompt = prompt)

print("Response form Ollama.qwen.3")
print("Response: ")