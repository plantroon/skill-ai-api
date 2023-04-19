# skill-ai-api
A skill for opsdroid for interacting with popular LLM's APIs with per-conversation threads in Matrix connector.

# How to use
Install and configure [node-chatgpt-api](https://github.com/waylaidwanderer/node-chatgpt-api). Then have a look at the example below. For continuous conversations (if/as supported by the API) you will need to have matrix connector and persistent storage configured in opsdroid. The upstream does not have any more universal conversations/threads so a Matrix-specific implementation was made.

- **hot-word** - the word that triggers the skill
- **api-url** - the URL where the API is reachable
- **prompt** - name of the field in the JSON payload that contains the text message for the API
- **response** - name of the field in the JSON payload that will contain the response from the API
- **params** - other parameters for the API
- **conversation_keys** - where supported, these will be saved to opsdroid memory to keep track of conversation in the thread

You can likely adjust the config for many REST APIs. In the example below there is a line called `llama` for use with [text-generation-webui](https://github.com/oobabooga/text-generation-webui). It barely works as the APIs that I found were not usable for chat, but with trial and error your prompts can get some use out of it. The example uses kobold API, which must be enabled by running text-gengeration-webui with `--extensions api` flag.

# Example config
```
skills:
  skill-ai-api:
    repo: "https://github.com/plantroon/skill-ai-api.git"
    branch: "main"
    apis:
      chatgpt: {hot-word: "chatgpt", api-url: "http://kubetest.lan:3009/conversation", prompt: "message", response: "['response']", params: { 'clientOptions': { 'clientToUse': 'chatgpt' }}, conversation_keys: {"conversationId", "conversationSignature", "clientId", "invocationId"}}
      bingai: {hot-word: "bing", api-url: "http://kubetest.lan:3009/conversation", prompt: "message", response: "['response']", params: { 'clientOptions': { 'clientToUse': 'bing' }}, conversation_keys: {"conversationId", "conversationSignature", "clientId", "invocationId"}}
      llama: {hot-word: "llama", api-url: "http://gpu-node03.lan:5000/api/v1/generate", prompt: "prompt", response: "['results'][0]['text']", params: {'max_new_tokens': 200, 'do_sample': false, 'temperature': 0.99, 'top_p': 0.9, 'typical_p': 1, 'repetition_penalty': 1.1, 'encoder_repetition_penalty': 1, 'top_k': 40, 'num_beams': 1, 'penalty_alpha': 0, 'min_length': 0, 'length_penalty': 1, 'no_repeat_ngram_size': 1, 'early_stopping': true, stopping_strings': { "\\n[", "\n[", "]:", "##", "###", "<noinput>", "\\end" }, seed': -1,  add_bos_token': true}}
```

# Preview of how it looks in Matrix
![matrix-threads-ai](https://upload.plantroon.com/Gsf.png)
