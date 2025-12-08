# LAMACOOP Documentation Generator

A lightweight, AI-assisted documentation generator for C projects.
This tool analyzes source code, extracts function-level information, and uses
LLM prompts to generate structured documentation, comments, and verification
reports.

The project is designed to be simple, modular, and completely open source.

## Features

- Function-level code parsing  
- AI-powered documentation  
- AI output verification  
- Prompt-based workflow  
- Test suite included

## Getting Started

### Prerequisites

- Python 3.8+
- Access to an Ollama endpoint

### Install Dependencies

```
python -m pip install -r requirements.txt
```

### Run Documentation Generator

```
python lamacoopDocgen.py <path_to_source_directory>
```

### Verify AI Output

```
python verifyAIOutput.py result/
```

## Running Tests

```
pytest .
```

## License

GPL2
