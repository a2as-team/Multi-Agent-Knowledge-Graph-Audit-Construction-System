# Ollama Setup Guide

This guide will help you set up Ollama with Llama 3.2 3B for use with the Schema Proposal Agent.

## Installation Steps

### 1. Install Ollama

**Windows:**
1. Download Ollama from: https://ollama.com/download/windows
2. Run the installer (`OllamaSetup.exe`)
3. Follow the installation wizard
4. Ollama will start automatically after installation

**Alternative (if installer doesn't work):**
```powershell
# Using winget (Windows Package Manager)
winget install Ollama.Ollama
```

### 2. Verify Installation

Open a new terminal/PowerShell and run:
```bash
ollama --version
```

You should see the version number (e.g., `ollama version is 0.x.x`)

### 3. Pull Llama 3.2 3B Model

```bash
ollama pull llama3.2:3b
```

This will download the model (approximately 2GB). Wait for it to complete.

### 4. Test Ollama Manually

```bash
ollama run llama3.2:3b "Hello, can you hear me?"
```

You should get a response from the model.

### 5. Verify Ollama is Running

Ollama runs as a service on Windows. To check if it's running:
- Open Task Manager
- Look for "Ollama" process
- Or check if `http://localhost:11434` is accessible

### 6. Test with Python Script

Run the test script:
```bash
python test_ollama_connection.py
```

## Troubleshooting

### Ollama not starting
- Check Windows Services: `services.msc` → Look for "Ollama"
- Manually start: Open terminal and run `ollama serve`

### Connection refused error
- Make sure Ollama is running: `ollama list` (should show installed models)
- Check if port 11434 is available
- Try restarting Ollama: Close and reopen the Ollama application

### Model not found
- Make sure you pulled the model: `ollama pull llama3.2:3b`
- Check installed models: `ollama list`

### Slow responses
- Llama 3.2 3B works best with GPU acceleration
- On CPU, expect 5-15 seconds per response
- Consider using a smaller model (1B) for faster responses: `ollama pull llama3.2:1b`

## Switching Back to Gemini

If you need to switch back to Gemini API, edit `src/utils/config.py`:

```python
# Change this line:
DEFAULT_MODEL = MODEL_OLLAMA_LLAMA_32_3B

# Back to:
DEFAULT_MODEL = MODEL_GEMINI_FLASH
```

Your Gemini API key is still in `.env` and will work when you switch back.

## Model Options

Available Ollama models you can use:

- `ollama/llama3.2:3b` - Current default (good balance)
- `ollama/llama3.2:1b` - Faster, less accurate
- `ollama/qwen2.5:7b` - More accurate, slower
- `ollama/qwen2.5:3b` - Alternative 3B model

To use a different model, update `DEFAULT_MODEL` in `src/utils/config.py` and pull the model with `ollama pull <model-name>`.

