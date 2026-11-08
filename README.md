# Romanian Text Editor

*A Romanian text editor powered by local LLMs. This showcase project focuses on layered architecture and the use of various design patterns while keeping dependencies to a minimum*

A Python text processing application that uses local Large Language Models (through Ollama) to work with Romanian text. This is a showcase project built with a focus on **clean architecture and minimal dependencies**. Main features:

- Strong focus on **architecture**, with an **easily extensible** modular approach and a variety of **design patterns**.
- It runs as a **command-line application** with three modes: fully **interactive**, **CLI with fallback** prompts and smart defaults, and **non-interactive** for automation.
- The app is primarily **config-driven**, with options for extending or customizing various elements directly through config or with minimal coding.
- Runs with **minimal dependencies** (only base Python 3.7+ and an Ollama server required). Running Ollama locally keeps your data on your computer.
- Offers several **Romanian text-processing capabilities** out of the box, using **locally run** models through Ollama. The default capabilities are:
  - **Add diacritics** - Restore proper Romanian characters (ă, â, î, ș, ț) to text missing them
  - **Summarize** - Generate concise summaries of Romanian documents  
  - **Edit and improve** - Refine text quality, style, and grammar
  - **Translate** - Bidirectional Romanian ↔ English translation
  - **Custom tasks** - Placeholder for custom tasks

Given the goals of the project, parts of it are over-engineered (e.g. the logger, config handling or startup sequence), but this is by design.

## Table of Contents

- [Quick Start](#quick-start)
- [Model Recommendations](#model-recommendations)
- [Usage Guide](#usage-guide)
  - [Parameter Types](#parameter-types)
  - [Interactive Mode](#interactive-mode-recommended-for-first-use)
  - [CLI Mode with Fallback](#cli-mode-with-fallback)
  - [Non-Interactive Mode](#non-interactive-mode-automation)
  - [Output Path Behavior](#output-path-behavior)
- [Customizing Task Prompts](#customizing-task-prompts)
- [Advanced Features](#advanced-features)
  - [Advanced: Custom Chunking Strategies](#advanced-custom-chunking-strategies)
  - [Console Output Modes](#console-output-modes)
- [Project Structure](#project-structure)
  - [Debugging & Logging](#debugging--logging)
- [Architecture & Design Decisions](#architecture--design-decisions)
  - [Why Minimal Dependencies?](#why-minimal-dependencies)
  - [Layered Architecture](#layered-architecture)
  - [Key Design Patterns](#key-design-patterns)
  - [Configuration-Driven Design](#configuration-driven-design)
- [Extending the Application](#extending-the-application)
  - [Adding a New Task](#adding-a-new-task)
  - [Adding a New Chunking Strategy](#adding-a-new-chunking-strategy)
  - [Other Possible Adaptations](#other-possible-adaptations)
- [Configuration Files](#configuration-files)
- [Testing](#testing)
- [Limitations & Scope](#limitations--scope)
- [Contact](#contact)
- [Acknowledgments](#acknowledgments)
- [License](#license)
- [Project Status](#project-status)

---


## Quick Start

**Prerequisites**: Python 3.7+ and Ollama installed

1. **Install and start Ollama**:
   ```bash
   # Download from https://ollama.ai, then:
   ollama serve
   
   # Then, pull a Romanian-capable model. Primarily tested
   # with the model jobautomation/OpenEuroLLM-Romanian:latest (~8GB). You can get it in ollama using:
   ollama pull jobautomation/OpenEuroLLM-Romanian:latest
   ```

2. **Clone and run the app**:
   ```bash
   git clone https://github.com/renitsa/RomanianTextEditor.git
   cd RomanianTextEditor
   python run.py
   ```

That's it. It should run on Python 3.7+ alone.

**Language and Model Flexibility:** You can use any other Ollama model with this application. The configuration supports different models and languages—simply adjust the model selection and modify task prompts in `config/text_actions_config.json` to adapt the app for other languages.

**Note on prompt language:** All text processing prompts are in English for broader accessibility. For Romanian-specific tasks, the quality difference between Romanian and English prompts should be minimal, as modern LLMs handle cross-lingual instructions well.

---

## Model Recommendations

The app was primarily tested with the model **jobautomation/OpenEuroLLM-Romanian:latest**, which offers excellent Romanian language support for its relatively small size (~8GB). While less widely known than models like Llama or Mistral, it's specifically trained for Romanian text and produces significantly better results for diacritics, translation, and text quality tasks.

**If you prefer mainstream models or have concerns about less common models:**
- **4GB+**: `llama3.2:3b` or `mistral:7b-instruct-q4_0` (decent Romanian, EU model)
- **8GB+**: `jobautomation/OpenEuroLLM-Romanian:latest` (recommended, Romanian-optimized), `gemma4:e2b`
- **16GB+**: `llama3.1:8b` or `mixtral:8x7b` (strong multilingual capabilities)

The examples in this documentation use the recommended Romanian-optimized model to showcase optimal results. All commands work with any model by simply changing the `--model` parameter.

---

## Usage Guide

Run the application with: `python run.py [parameters]` (see examples below)
The application will start in one of the three modes - **interactive**, **command-line with fallback to interactive** or **command-line without fallback** depending on the parameters that you use. These modes are explained in more detail in the section after parameter types. 

### Parameter Types

There are 3 types of parameters:

**Required Parameters** (must be provided for processing):
- `--task TASK` - Processing task (diacritics, summarize, edit, translate_ro_en, translate_en_ro, custom)
- `--model MODEL` - Ollama model to use
- `--input FILE` OR `--text "TEXT"` - Input source (file path or direct text)

**Optional Parameters** (have smart defaults):
- `--output FILE` - Output file path (default: console for text input, auto-generated for file input)
- `--console` - Force console output instead of file (when input is from file)
- `--chunkers STRATEGY [...]` - Override chunking strategies (default: from config)

**Utility Parameters** (control runtime behavior):
- `--verbose` - Enable detailed logging
- `--non-interactive` - Disable all prompts (fails if any of the required parameters is missing)

---

### Interactive Mode (Recommended for First Use)

Run without any processing arguments to get prompted for all parameters. Best for first-time users and exploratory workflows.

```bash
python run.py
```

You'll be guided through:
1. **Task selection** - Choose from available tasks
2. **Model selection** - Pick from your installed Ollama models  
3. **Input source** - File path or paste text directly
4. **Output destination** - Save to file or display in console

**Note:** Utility flags like `--verbose` are always respected. Run `python run.py --verbose` for interactive prompts with detailed logging.

---

### CLI Mode with Fallback

Provide some arguments and get prompted only for missing required parameters. Optional parameters use smart defaults. Best for quick iterations when you know most details but not all.

```bash
# Partial info - will prompt for missing model
python run.py --task diacritics --input input/luceafarul.txt

# Complete specification
python run.py --task summarize --model jobautomation/OpenEuroLLM-Romanian:latest --input input/luceafarul.txt --console

# Direct text input (defaults to console output)
python run.py --task translate_ro_en --model jobautomation/OpenEuroLLM-Romanian:latest --text "Bună ziua! Cum vă numiți?"

# With verbose logging
python run.py --task edit --model jobautomation/OpenEuroLLM-Romanian:latest --input input/luceafarul.txt --verbose
```

---

### Non-Interactive Mode (Automation)

Use `--non-interactive` when all required parameters must be specified upfront (optional parameters still use defaults). Best for automation.

```bash
# All required parameters specified, output auto-generated
python run.py --task diacritics --model jobautomation/OpenEuroLLM-Romanian:latest \
  --input input/luceafarul.txt --non-interactive

# With explicit output file
python run.py --task summarize --model jobautomation/OpenEuroLLM-Romanian:latest \
  --input document.txt --output summary.txt --non-interactive

# Direct text input (output defaults to console)
python run.py --task translate_ro_en --model jobautomation/OpenEuroLLM-Romanian:latest \
  --text "Bună ziua!" --non-interactive
```

**Behavior:** Fails immediately with clear error message if any required parameter is missing. No prompts occur. Optional parameters use defaults. 

---

### Output Path Behavior

The application uses smart defaults for output paths based on your input method:

**File Input** (`--input file.txt`):
- **Default**: Auto-generates path in `./output/` directory with pattern: `{basename}_{task}_{timestamp}.txt`
- **Override**: Use `--output output/file_at_custom_path.txt` to specify exact location
- **Console**: Use `--console` to skip file output entirely and output to console instead

**Text Input** (`--text "..."`):
- **Default**: Outputs to console (no file created)
- **Override**: Use `--output file.txt` to save to file instead
- **Rationale**: Direct text input typically means quick testing/exploration

**Interactive Mode**:
- Always prompts for output preference: save to file (with auto-generated or custom path) or display in console

This behavior ensures sensible defaults while giving full control when needed. The output directory and filename patterns can be customized in `config/file_config.json`.

---

## Customizing Task Prompts

Task prompts are defined in `config/text_actions_config.json`. To customize:

```json
{
  "DIACRITICS": {
    "DESC": "Add Romanian diacritics to text",
    "PROMPT": "Your custom prompt here...",
    "CHUNKERS": ["sentence_split", "size_optimizing"],
    "INPUT_LANGUAGE": "ro"
  }
}
```

**Note:** To disable chunking for a specific task in config, use an empty list: `"CHUNKERS": []`

To add a new task, you only need a new entry in `text_actions_config.json`. It then shows up in the interactive menu and in `--task`. The CLI task name is the lower-case config key (`GRAMMAR_CHECK` becomes `--task grammar_check`). A task that needs extra behaviour can add a small processor class. See [Extending the Application](#extending-the-application) for details.

> **Note**: Command-line prompt override is intentionally not supported to keep the application config-driven and encourage tested, reusable prompts.

---

## Advanced Features

### Advanced: Custom Chunking Strategies

Large documents are automatically chunked for processing. You can control the strategy:

```bash
# Use sentence-based chunking (better for translations)
python run.py --task translate_ro_en --input input/luceafarul.txt --chunkers sentence_split --console

# Combine multiple strategies (applied in order)
python run.py --task summarize --input input/luceafarul.txt --chunkers paragraph_split size_optimizing --console

# Disable chunking entirely (process entire text as single chunk)
python run.py --task diacritics --input input/luceafarul.txt --chunkers none --console

# Available chunking strategies:
# - line_split: Split on line breaks (single Enter)
# - paragraph_split: Split on paragraph breaks (good for summarization)
# - sentence_split: Split on sentence boundaries (good for translation)
# - size_optimizing: Ensure chunks don't exceed max size
# - none: Disable chunking (process entire text as single chunk)
```

Chunking configuration is in `config/text_processing_config.json`:
```json
{...
  "STRINGSPLIT_MIN_SIZE": 20,
  "STRINGSPLIT_MAX_SIZE": 2000,
  "SENTENCESPLIT_MIN_SIZE": 10,
  "SENTENCESPLIT_MAX_SIZE": 800,
  ...
}
```

### Console Output Modes

The `--console` flag sends output to stdout (screen) instead of a file:

```bash
# Standard console output
python run.py --task diacritics --input text.txt --console

# Combine with verbose mode to see processing details
python run.py --task summarize --input doc.txt --console --verbose

# No output file needed in interactive mode either:
python run.py
# When prompted for the output destination, choose "2. Display in console"
```

---

## Project Structure

```
RomanianTextEditor/
├── run.py                          # Entry point
├── config/                         # JSON configuration files
│   ├── llm_services_config.json    # Ollama connection settings
│   ├── text_actions_config.json    # Task prompts and descriptions
│   ├── text_processing_config.json # Chunking parameters
│   ├── file_config.json            # File I/O settings
│   └── logging_config.json         # Logging configuration
│
├── input/                          # Input files directory
├── output/                         # Generated output directory
├── logs/                           # Runtime logs (created automatically)
├── tests/                          # unit, integration and end-to-end tests
├── extended_documentation/         # Extra notes on architecture and tests
├── QUICK_START.md                  # Short getting-started guide
│
└── src/                            # Source code
    ├── app/                        # Application layer
    │   ├── parameter_collection/   # CLI and interactive parameter gathering
    │   ├── exceptions.py           # Application exceptions (UserCancelled)
    │   ├── startup_manager.py      # Phased initialization coordinator
    │   ├── text_processing_app.py  # Main application facade
    │   ├── path_manager.py         # File path handling
    │   └── processor_factory.py    # Task discovery and processor creation
    │
    ├── config/                     # Configuration and validation
    │   ├── app_config.py           # Configuration singleton
    │   └── config_data_validator.py # Config validation logic
    │
    ├── services/                   # External service integrations
    │   └── ollama_service.py       # Ollama HTTP API client (urllib-based)
    │
    ├── text_processor/             # Text processing core
    │   ├── processor.py            # Config-driven TextProcessor, task registry, DiacriticAdder example
    │   ├── chunker.py              # Text chunking with strategy pattern
    │   ├── workflow.py             # Processing orchestration
    │   └── text_io.py              # Text reading and writing
    │
    └── utils/                      # Shared utilities
        ├── app_logger.py           # Two-stage logging system
        ├── dict_utils.py           # DotDict for dot access
        └── file_utils.py           # File I/O helpers
```

**Testing**: Comprehensive test suite with 300+ test cases covering unit, integration, and end-to-end scenarios.

---

### Debugging & Logging

The application implements **extensive logging** to help you understand what's happening under the hood:

- **Startup logs**: Capture initialization sequence and configuration loading
- **Runtime logs**: Track text processing, chunking, and LLM interactions  
- **Log file**: Default location is `logs/application.log` (configurable in `logging_config.json`)
- **Verbose mode**: Use `--verbose` flag for detailed console output

---

## Architecture & Design Decisions

### Why Minimal Dependencies?

The primary goal was to keep the environment **lightweight and dependency-free**. Using Ollama as a separate service means you **don't need PyTorch, TensorFlow, or other heavy ML frameworks** in your Python environment. This was both a technical requirement and a personal challenge to demonstrate what's possible with just the standard library.

This approach has the following advantages: 
1. **Deployment simplicity** - No dependency conflicts, no virtual environment required. The app should be easy to deploy for users that are not very technically-proficient. 
2. **Educational value** - Understanding how various app elements work under the hood 
3. **Full control** - No black-box library behaviors, explicit implementations

**Trade-offs made**:
- `urllib` instead of `requests` or `ollama` → More verbose HTTP code, but no dependencies. This is used strictly for communicating with the local ollama server, and it also makes the code more prone to failure in case ollama makes changes in its internal processes in the future. However, such errors should be easily fixable if/when they would occur.
- `dataclasses` with custom validation instead of `pydantic` → Manual validation logic, but stdlib-only
- `unittest` instead of `pytest` → Less elegant, but no external test runner

This makes some parts over-engineered for a simple LLM wrapper, but this is deliberate and in line with the project goals of demonstrating patterns and practices.

### Layered Architecture

The application follows a clean layered architecture:
- **Application Layer** (`src/app/`) - Startup, parameter collection, factory
- **Processing Core** (`src/text_processor/`) - Text processing, chunking, workflow
- **Services Layer** (`src/services/`) - External API clients (Ollama)
- **Cross-cutting** - Configuration, logging, utilities

Each layer depends only on layers below it, ensuring clean separation of concerns.

### Key Design Patterns

**1. Phased Initialization**
The application startup follows a 5-phase sequence with validation at each step:

```python
1. Bootstrap validation → Check Python version, file permissions
2. Startup logging → Initialize startup logger for early diagnostics
3. Configuration loading → Load and validate all JSON configs
4. Application logging → Transfer startup logs to main logger, configure runtime logging
5. Finalize startup → Check Ollama availability (warning only), mark startup complete
```

**2. Two-Stage Logging**
- **Startup logger** - Captures initialization messages before configuration loads
- **Runtime logger** - Full-featured logging with config-driven levels, file rotation, verbose mode

If startup fails, the bootstrap logger automatically dumps the current logs to file. Upon first successful startup, the log dump file is automatically moved to main log and then removed.

This pattern ensures you can see what's happening even if config loading fails. If you want to understand what the app is doing under the hood, you can check the main log file (default is application.log)

**3. Module-Level Singletons**
Configuration, logging, and the Ollama service use module-level singletons.
This pattern provides global access to shared resources during runtime while maintaining control over initialization timing.

**4. Factory Pattern**
`ProcessorFactory` creates the text processor for a task name (diacritics, summarize, translate, etc.). The list of tasks comes from `config/text_actions_config.json`, so adding a task is a config change; the factory uses the registered class if the task has one and the default `TextProcessor` otherwise.

**5. Strategy Pattern**
Text chunking uses interchangeable algorithms (sentence split, paragraph split, size optimizing) that can be selected at runtime. Each strategy implements the same interface but with different splitting logic. This eliminates conditional logic and follows the Open/Closed Principle.

**6. Registry Pattern**
The application uses registries to map string names to implementations, enabling runtime component selection without conditional logic:
- `CHUNKER_REGISTRY` - Maps chunker names to strategy classes (e.g., "sentence_split" → SentenceSplitStrategy)
- `TASK_REGISTRY` - Maps task names to processor classes that add custom behaviour (e.g., "diacritics" → DiacriticAdder). Classes register themselves with the `@register_task("name")` decorator when `processor.py` is imported, so the registry is rebuilt in memory on every run.

This pattern makes adding new components straightforward - just register them in the appropriate dictionary.

**7. Builder Pattern**
`TextChunker` builds a processing pipeline incrementally using method chaining:
```python
chunker.add_strategy(strategy1).add_strategy(strategy2)
```
Each strategy is added to the pipeline, which then processes text through all strategies in sequence.

**8. Template Method Pattern**
Two places use it:
- `TextProcessor.process_text()` fixes the order of the steps for every chunk (`preprocess` → LLM call → `postprocess`). Task subclasses only override the hooks.
- `BaseParameterCollector` defines a template workflow for parameter collection that CLI and Interactive collectors implement differently (common workflow in the base class, subclasses override specific collection methods).

**9. Facade Pattern**
`TextProcessingApplication` provides a simplified interface to the complex subsystem of processors, chunkers, readers, and writers. Users interact with one clean API while the facade coordinates multiple components.

**10. Dependency Injection**
Configuration and loggers are injected through optional constructor parameters, with the module-level singleton as the fallback (`self.config = config if config is not None else get_app_config()`). This keeps classes usable on their own and easy to test with mocks.

### Configuration-Driven Design

All task prompts and processing parameters live in JSON files under `config/`. This means:
- Change prompts without touching code
- Adjust chunking behavior via config
- Easy to experiment with different settings

See the [Customizing Task Prompts](#customizing-task-prompts) section for configuration examples.

---

## Extending the Application

The architecture makes adding new functionality straightforward:

### Adding a New Task

**1. Add configuration** to `config/text_actions_config.json`. The key is the task name in upper case; the command-line name is the same in lower case:
```json
{
  "GRAMMAR_CHECK": {
    "DESC": "Check Romanian grammar",
    "PROMPT": "Check and correct grammar in this Romanian text:",
    "CHUNKERS": ["sentence_split"],
    "INPUT_LANGUAGE": "ro"
  }
}
```

Done. The task now appears in the interactive menu and works with `--task grammar_check` in CLI mode. The prompt, chunking and language all come from the config, so most tasks need nothing else.

**2. (Optional) Add behaviour** when a task needs more than a prompt. Subclass `TextProcessor` in `src/text_processor/processor.py`, override a hook, and register the class under the task name:
```python
@register_task("grammar_check")
class GrammarChecker(TextProcessor):
    def postprocess(self, text: str) -> str:
        # Runs on the LLM answer of every chunk, e.g. strip a leading "Here is the corrected text:"
        return text.strip()
```

The hooks are `preprocess(text)` (runs before the LLM call) and `postprocess(text)` (runs after it); both return the text unchanged by default. `DiacriticAdder` is a working example: it replaces the cedilla letters (ş, ţ) that models often produce with the correct comma-below ones (ș, ț). A registered task must have a config entry, which startup checks.

Because the decorator runs when `processor.py` is imported, keep task classes in that module (or import theirs from it) so they are always registered.

### Adding a New Chunking Strategy

Implement the `ChunkStrategy` interface in `src/text_processor/chunker.py`:

```python
class CustomStrategy(ChunkStrategy):
    def __init__(self, language: str = "ro", **kwargs):
        super().__init__(**kwargs)  # Required — initializes logger and config

    def apply(self, chunks: List[str]) -> List[str]:
        # Your chunking logic here
        return processed_chunks
```

Then add it to `CHUNKER_REGISTRY` (defined at the bottom of the same file):

```python
CHUNKER_REGISTRY['custom_split'] = CustomStrategy
```

Now use it: `--chunkers custom_split`

### Other Possible Adaptations

The current architecture allows for relatively easy modifications beyond text processing:

- **Change processing language**: With minimal config changes and a different model, you can adapt the app to process texts in other languages (Spanish, French, German, etc.)
- **Coding assistant**: The architecture could be adapted to create a basic, locally-run coding assistant by changing prompts, task definitions and model
- **Domain-specific processing**: Add tasks for legal documents, medical texts, or technical documentation, usually just with a new prompt in the config, or a small processor subclass for custom pre/post-processing

These modifications would be straightforward given the modular design and would primarily require configuration changes. Tasks that do not fit the read → chunk → process → write pipeline (for example a multi-turn chatbot) would need their own workflow next to `ProcessingWorkflow`.

**Input formats.** `TextReader` has placeholder readers for `.pdf`, `.docx` and `.html` that return nothing, because real readers need extra libraries, which this project avoids. Those extensions are listed in `SUPPORTED_DOCUMENT_EXTENSIONS` in `file_config.json`; the app does not offer such files and tells you to convert them. A fork that adds a reader can make them available.

---

## Configuration Files

All configuration is externalized in JSON format:

**`llm_services_config.json`** - Ollama connection:
```json
{
  "OLLAMA": {
    "url": "http://localhost:11434",
    "generate_timeout": 300,
    "check_timeout": 5
  }
}
```

**`text_actions_config.json`** - Task definitions and prompts. Each key is a task; its lower-case form is the `--task` name:
```json
{
  "TASK_NAME": {
    "DESC": "Description shown in CLI help",
    "PROMPT": "Do this action, following these rules, on the text below:",
    "CHUNKERS": ["strategy1", "strategy2"],
    "INPUT_LANGUAGE": "ro"
  }
}
```
Use `"CHUNKERS": []` to disable chunking for a task. Chunker names are checked at startup.

**`text_processing_config.json`** - Chunking parameters:
```json
{
  "STRINGSPLIT_MIN_SIZE": 20,
  "STRINGSPLIT_MAX_SIZE": 2000,
  "SENTENCESPLIT_MIN_SIZE": 10,
  "FALLBACK_CHUNK_SEPARATOR": "\n\n",
  "COMMON_RO_ABBREVIATIONS": ["Dr.", "nr.", "art."]
}
```

**`file_config.json`** - Folders, supported file types and output naming. Output files are named `{input name}{OUTPUT_SUFFIX_SEPARATOR}{task}{OUTPUT_SUFFIX_SEPARATOR}{timestamp}{extension}`, using these keys:
```json
{
  "OUTPUT_SUFFIX_SEPARATOR": "_",
  "OUTPUT_TIMESTAMP_FORMAT": "%Y%m%d_%H%M%S",
  "DEFAULT_OUTPUT_FILENAME": "output.txt",
  "MAX_FILENAME_LENGTH": 255
}
```

**`logging_config.json`** - Logging behavior:
```json
{
  "LOG_TO_CONSOLE": true,
  "LOG_TO_FILE": true,
  "CONSOLE_LEVEL": "INFO",
  "FILE_LEVEL": "DEBUG"
}
```

---

## Testing

The project includes a comprehensive test suite with 300+ test cases using Python's `unittest` framework, organized into unit, integration, and end-to-end categories.

```bash
# Run all tests
python -m unittest discover -s tests -p "test_*.py" -v

# Run specific test module
python -m unittest tests.unit.test_startup_manager
```

**Testing approach**: I initially developed tests inline (using `if __name__ == "__main__"` blocks) during development, then extracted them into separate test files with AI assistance. The test suite covers parameter collection, text processing workflows, configuration loading, and chunking strategies.

**Test organization**:
- `tests/unit/` - Isolated component tests
- `tests/integration/` - Component interaction tests  
- `tests/e2e/` - Complete workflow tests
- `tests/fixtures/` - Shared test data (mock configs, sample texts, test files)

---

## Limitations & Scope

The language capabilities of this app work well but are **deliberately limited in scope**. This is a showcase project demonstrating clean architecture patterns, not a comprehensive NLP toolkit.

Known limitations:
- **Layout is preserved on a best-effort basis.** Each chunk is sent to the model as written, and the original whitespace between chunks (blank lines, line breaks, spaces) is restored in the output. The model may still change the layout inside a chunk. If a custom chunking strategy rewrites the text so that chunks cannot be matched to the input, chunks are joined with `FALLBACK_CHUNK_SEPARATOR` from `text_processing_config.json` (default: a blank line).
- **Failed chunks are kept as they were.** If the model fails on a chunk (for example a timeout), the original text is kept for that chunk and a warning shows how many chunks were affected. If every chunk fails, nothing is written and the run reports an error.
- **Quality depends on the model.** For example, a small model may change words when asked only to add diacritics. Check important results.
- **Only plain-text inputs** (`.txt`, `.md`, `.markdown`) are read. PDF, DOCX and HTML would need extra libraries.

---

## Contact

For questions, feature requests, or custom development inquiries:

- **GitHub Issues**: [https://github.com/renitsa/RomanianTextEditor/issues](https://github.com/renitsa/RomanianTextEditor/issues) (requires a GitHub account)
- **LinkedIn**: [linkedin.com/in/lucian-renitsa](https://www.linkedin.com/in/lucian-renitsa/)

*For commercial applications or custom implementations with advanced features, consulting services are available upon request.*

---

## Acknowledgments

- **Ollama** - For making local LLM inference accessible and easy to use
- **OpenEuroLLM-Romanian** - Excellent Romanian language model by jobautomation
- **Python community** - For the comprehensive standard library that made this possible

If you create your own variants based on this project, I would appreciate mentioning the original project and author in your documentation.

---

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) - see the [LICENSE](LICENSE) file for details.

**In brief:** You are free to use, modify, and distribute this software, but any derivative works must:
- Be released under GPL-3.0 and remain open source
- Retain copyright notices and attribute the original authors
- Include the full GPL-3.0 license text
- Document any changes made to the source code

This ensures the software and its derivatives remain free and open for everyone.

---

## Project Status

This is a **showcase/portfolio project** demonstrating software engineering practices and architectural patterns. It is not currently under active maintenance or extension beyond its current scope.

The codebase is provided as-is for educational purposes and as a foundation for your own projects.
