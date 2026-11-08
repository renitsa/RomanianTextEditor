# Quick Start Guide

Get the Romanian Text Editor running in under 5 minutes.

## Prerequisites

You need two things:
- **Python 3.7+** (check: `python --version`)
- **Ollama** installed and running ([download here](https://ollama.ai))

## Installation Steps

### 1. Install and Start Ollama

Ollama is a popular and reliable server that allows running LLMs locally. 

```bash
# Download from https://ollama.ai and install, then start the service:
ollama serve
```
Keep this terminal running.

### 2. Pull a Romanian Model

In a new terminal:

```bash
# Recommended model (8GB, good Romanian support):
ollama pull jobautomation/OpenEuroLLM-Romanian:latest

# Alternative smaller model (4GB, decent Romanian ok for testing):
ollama pull mistral:7b-instruct-q4_0
```

### 3. Get the Application

```bash
git clone https://github.com/renitsa/RomanianTextEditor.git
cd RomanianTextEditor
```

That's it - you only need Python 3.7+ to run, with no additional dependencies to install.

## Your First Run

### Interactive Mode (Recommended)

```bash
python run.py
```

The app will guide you through:
1. **Choose a task**: diacritics, summarize, edit, translate, or custom
2. **Select a model**: from your installed Ollama models
3. **Provide input**: file path or paste text directly
4. **Choose output**: save to file or display in console

### Command-Line Mode

Try these examples:

```bash
# Add diacritics to text (uses interactive prompts for missing parameters)
python run.py --task diacritics --input input/luceafarul.txt

# Complete specification with console output
python run.py --task summarize --model jobautomation/OpenEuroLLM-Romanian:latest --input input/luceafarul.txt --console

# Translate direct text
python run.py --task translate_ro_en --model jobautomation/OpenEuroLLM-Romanian:latest --text "Bună ziua! Cum vă numiți?"

# Automated mode (no prompts)
python run.py --task diacritics --model jobautomation/OpenEuroLLM-Romanian:latest --input input/luceafarul.txt --non-interactive
```

## Common Issues

### "App seems to get stuck"

**Problem:** The application appears unresponsive during model selection or processing.

**Common causes:**
- **Model loading**: On first use, models must be loaded into memory (several seconds to minutes depending on model size and hardware)
- **Slow inference**: Processing speed depends on hardware capabilities and model size
- **Model selection delay**: A brief delay (2-5 seconds) occurs when fetching the model list from Ollama

**Solutions:**
1. **Be patient** - Check if processing is happening:
   - Use `--verbose` flag to see progress: `python run.py --verbose`
   - Check logs in `logs/application.log` for activity
2. **Test with a smaller model** - Try `llama3.2:3b` or `mistral:7b-instruct-q4_0` to isolate hardware issues
3. **Understand GPU/CPU behavior** - Models that don't fit in GPU memory will run on CPU (much slower but functional if they fit in RAM)
4. **Start with small inputs** - Test with short text or small files before processing large documents

### "Ollama service not accessible"

**Problem:** The app can't connect to Ollama.

**Solutions:**
1. Make sure Ollama is running: `ollama serve`
2. Check it's accessible: `curl http://localhost:11434/api/tags`
3. If using a custom URL, update `config/llm_services_config.json`

### "Model not found"

**Problem:** The specified model isn't installed.

**Solutions:**
1. List installed models: `ollama list`
2. Pull the model: `ollama pull model-name`
3. Or run without `--model` flag to get a selection prompt

### "File not found: input/luceafarul.txt"

**Problem:** Test input file doesn't exist.

**Solutions:**
1. Create the `input/` directory: `mkdir input`
2. Add your own text file, or
3. Use `--text "your text here"` instead of `--input`

## Usage Modes at a Glance

| Mode | When to Use | How to Activate |
|------|-------------|-----------------|
| **Interactive** | First-time use, exploring features | `python run.py` |
| **CLI with Fallback** | Quick iterations, know most details | `python run.py --task X --input Y` |
| **Non-Interactive** | Automation, scripting | Add `--non-interactive` flag |

## Parameter Types

**Required** (must be provided):
- `--task` - What to do (diacritics, summarize, edit, translate_ro_en, translate_en_ro, custom)
- `--model` - Which Ollama model to use
- `--input FILE` or `--text "TEXT"` - What to process

**Optional** (have smart defaults):
- `--output FILE` - Where to save (default: console for text input, auto-generated for file input)
- `--console` - Force console output (when using file input)
- `--chunkers STRATEGY [...]` - Override chunking (default: from config)

**Utility**:
- `--verbose` - Detailed logging
- `--non-interactive` - No prompts (fail if required params missing)

## Next Steps

### Learn More

- **Full Documentation**: See [README.md](README.md) for complete usage guide
- **Customize Prompts**: Edit task prompts in `config/text_actions_config.json`
- **Add Custom Tasks**: See "Extending the Application" section in README


### Explore Advanced Features

```bash
# Use different chunking strategies
python run.py --task translate_ro_en --model jobautomation/OpenEuroLLM-Romanian:latest --input input/luceafarul.txt --chunkers sentence_split --console

# Disable chunking for small files
python run.py --task diacritics --model jobautomation/OpenEuroLLM-Romanian:latest --input input/luceafarul.txt --chunkers none --console

# Enable verbose logging to see what's happening
python run.py --task summarize --model jobautomation/OpenEuroLLM-Romanian:latest --input input/luceafarul.txt --console --verbose
```

## Tips

1. **Start with Interactive Mode** - It's the easiest way to learn what parameters are available
2. **Use `--verbose` flag** - See detailed processing steps and troubleshoot issues
3. **Check logs** - Application log is in `logs/application.log` by default
4. **Test with small files first** - Large documents take longer to process
5. **Console output is instant** - Use `--console` flag to see results immediately without creating files

## Model Recommendations

The application was tested primarily with **jobautomation/OpenEuroLLM-Romanian:latest** and this is the recommended small model for best results. While less widely known than Llama or Mistral, it's specifically trained for Romanian text and produces significantly better quality for the available tasks.

**Model options by VRAM:**
- **4GB+**: `llama3.2:3b` or `mistral:7b-instruct-q4_0` (decent Romanian, EU model)
- **8GB+**: `jobautomation/OpenEuroLLM-Romanian:latest` (recommended, Romanian-optimized), `gemma4:e2b`
- **16GB+**: `llama3.1:8b` or `mixtral:8x7b` (strong multilingual capabilities)

All examples in this guide use the Romanian-optimized model. Simply change `--model` to use a different one.

## Getting Help

- **Command help**: `python run.py --help`
- **Check logs**: `logs/application.log`
- **Configuration**: All settings in `config/` directory (JSON files)
- **Issues**: Check GitHub Issues for support

---

**Ready to go?** Start with: `python run.py`
