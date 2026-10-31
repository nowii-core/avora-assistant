<div align="center">
  <h1><img src="assets/avora.svg" width="30" height="30" alt="Avora logo"> Avora</h1>
  <p><strong>A private AI assistant that runs on your computer.</strong></p>
  <p>Version 1.4.0 · nowii-core · Local Ollama · SQLite</p>
</div>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-007ec6?style=for-the-badge" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/AI%20Runtime-Ollama-111111?style=for-the-badge" alt="Ollama">
  <img src="https://img.shields.io/badge/Storage-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-000000?style=for-the-badge" alt="Platform support">
</p>

<p align="center">
  <a href="#overview">Overview</a> |
  <a href="#key-features">Features</a> |
  <a href="#quick-start">Quick Start</a> |
  <a href="#model-selection">Models</a> |
  <a href="#privacy--security">Privacy</a> |
  <a href="#development">Development</a> |
  <a href="#contact--support">Contact</a>
</p>

---

## Overview

Most AI assistants rely on cloud services, accounts, or API keys. **Avora takes a local-first approach:** it brings a complete AI chat experience to your own computer, powered by open-weight models running through [Ollama](https://ollama.com).

Avora includes streaming responses, conversation history, file and image attachments, web search, image generation, voice interaction, and an optional agent that can use tools. Your conversations and application data are stored locally. No account or cloud API key is required to use a local model.

Internet access is only used by features that need it, such as web search, neural text-to-speech, and optional online image generation. These integrations are described in the app before use.

```text
Avora
  ├── Local AI chat with streaming responses
  ├── Ollama model runtime
  ├── Tool-using agent and web search
  ├── Voice, images, and file attachments
  └── Local conversation history with SQLite
```

Avora's application code (server, interface, and integrations) is released under the MIT License. Language models, voices, and external services are provided by third parties and remain subject to their own licenses and terms.

---

## Key Features

- **Local AI:** runs open-weight language models through Ollama on your computer. Chatting with a local model does not require a cloud account.
- **Agent with tools:** when Agent mode is enabled, Avora can decide whether to run local Python tools for calculations, data analysis, and charts, or search the web. Tool activity is shown in the chat. Tool calling requires a compatible model, such as Qwen3 or Llama 3.1 and later.
- **Python sandbox:** runs model-generated code in a separate process with time, memory, and file limits and no network access. This is a basic containment measure, not a security boundary against malicious code.
- **Configurable personas:** switch between General, Code Assistant, Creative Writer, Data Analyst, Tutor, Business Advisor, or a custom role.
- **Streaming responses:** responses appear as they are generated and can be stopped at any time. Long answers can continue automatically instead of ending prematurely.
- **Voice conversation:** speak to Avora and receive spoken responses. Choose between system voices, which can work offline, and Italian neural voices through `edge-tts`. Microphone recognition depends on the browser and its speech-recognition support.
- **Images and attachments:** attach up to four images per message, including images pasted or dragged into the chat, as well as text and code files. Image understanding requires a compatible vision model, such as `qwen3-vl:2b`.
- **Image generation:** create diagrams and illustrations from the chat. Avora can generate local SVG artwork, use a compatible local image model through Ollama, or use optional online providers when enabled.
- **Integrated web search:** look up current information and display clickable sources. If search is unavailable, Avora reports the issue instead of presenting unavailable results as verified.
- **Artifact previews:** preview HTML, SVG, and Markdown in a dedicated panel, with options to view, copy, and download the result. HTML previews are isolated and do not execute embedded scripts.
- **Context awareness:** see how much of the model's context window is being used. When a conversation gets long, summarize it into a new chat.
- **Local conversation history:** SQLite stores conversations and related data. Search, rename, export, or delete conversations from the interface.
- **Customizable interface:** choose light, dark, or automatic themes, adjust text size, and organize work with projects and reusable instructions.
- **Optional token limits:** set a token allowance over a three-hour window using Standard, Extended, or Maximum profiles. This is an optional local control and does not add usage fees.
- **Guided model setup:** choose from model profiles and download models from inside the app, with installation progress displayed in the interface.
- **Demo mode:** explore the interface without installing Ollama or downloading a model. Demo replies are preset examples and are labelled as such.

---

## Quick Start

### Requirements

- macOS, Windows, or Linux.
- Python 3.10 or later.
- [Ollama](https://ollama.com/download) installed and running to use local AI models.
- Enough free disk space for the model you choose. Download sizes are approximate.

### 1. Get the project

Clone or download this repository from GitHub, then open the project folder on your computer.

### 2. Start Avora

**macOS**

Double-click `Avvia-Avora-Mac.command`, or run it from Terminal:

```bash
bash Avvia-Avora-Mac.command
```

If Ollama is not installed, the launcher opens the official download page.

**Windows**

Double-click `Avvia-Avora-Windows.bat`. If required, the launcher can attempt to install Python and Ollama through `winget`.

**Linux**

```bash
bash start-linux.sh
```

The launcher starts the local server and opens the app in your browser. On first launch, the setup guide helps you configure Avora and download a suitable model.

### 3. Open the app

The default local address is:

```text
http://127.0.0.1:8765
```

### Demo Mode

To explore the interface without Ollama or a downloaded model:

```bash
# macOS
bash Avvia-Demo-Mac.command

# Linux or manual launch
python3 run.py --demo
```

On Windows, double-click `Avvia-Demo-Windows.bat`.

Demo replies are preset examples. They are labelled as demo content and are not generated by an AI model.

### Start the server manually

```bash
python3 run.py
```

Useful options:

```bash
python3 run.py --demo
python3 run.py --host 127.0.0.1 --port 8765
python3 run.py --no-browser
```

---

## Model Selection

Avora includes three starter profiles based on Qwen3 models. Select a profile in Settings, or use a compatible model tag from the Ollama library through the advanced settings.

| Profile | Ollama model | Approx. download | Recommended RAM | Best for |
| :--- | :--- | :--- | :--- | :--- |
| Fast | `qwen3:1.7b` | ~1.4 GB | 8 GB | Quick replies and simple requests |
| Balanced | `qwen3:4b` | ~2.6 GB | 8 GB or more | Everyday use and coding |
| Quality | `qwen3:8b` | ~5.2 GB | 16 GB or more | More demanding prompts and writing |

Sizes are approximate. Actual memory usage depends on the model, context length, and your system. Smaller local models may be less capable or accurate than large cloud-based models.

Image understanding requires a vision-capable model, such as `qwen3-vl:2b`, which can be downloaded separately when needed.

---

## Voice & Images

### Voice

Select **Voice**, speak, and pause briefly. Avora processes your request and can begin speaking while the rest of the response is still being generated.

- **System voice:** uses voices available on your device and does not require an online text-to-speech service.
- **Neural voice:** uses `edge-tts` for Italian neural voices. The text to be spoken is sent to the Microsoft Edge TTS service.
- **Speech recognition:** depends on your browser and its speech APIs. Some browsers may use an external service for recognition.

The macOS launcher attempts to install the optional voice support listed in `requirements-voice.txt` when a network connection is available.

### Images

Avora can create diagrams, illustrations, and images from chat prompts.

- Diagrams and vector illustrations can be generated locally as SVG files.
- Local photographic image generation is available through a compatible Ollama image model, such as `x/flux2-klein`. The model download requires several gigabytes of disk space.
- Optional online generation through AI Horde sends the prompt anonymously to volunteer-run workers after user consent. Generation time can vary.
- Other external providers may be configured by the user and are subject to their own terms and settings.

Before enabling an online feature, review the information shown by Avora. Prompts, text for speech, or other data required by that feature may be sent to the named service.

---

## Privacy & Security

Avora is designed to keep application data on your device and communicate with a local model runtime.

- **Local server:** the interface is served locally at `127.0.0.1:8765` by default.
- **Local model:** chat requests are sent to Ollama at `127.0.0.1:11434`.
- **Database:** conversations are stored in `data/nautilus.sqlite3` (a legacy filename).
- **Attachments and generated content:** stored in local directories under `data/`.
- **Optional online integrations:** web search, neural text-to-speech, and online image generation require external connections. Their use is described in the app and in this README.
- **Keep private data private:** do not publish your local database, attachments, configuration files, or provider credentials.

The Python sandbox limits some resources and disables network access, but it should not be treated as a secure environment for running hostile code. AI models can also produce incorrect information. Verify important results, especially for medical, legal, financial, or technical decisions.

---

## Development

### Run the tests

From the project root:

```bash
python3 -m unittest discover -s tests -v
```

### Optional voice dependency

To install neural voice support manually:

```bash
python3 -m pip install -r requirements-voice.txt
```

### Transformer training lab

The repository also includes a separate educational path for training a small Transformer from scratch. It is not Avora's default model and is not intended to match the capabilities of large commercial AI assistants.

Training dependencies are separate from those needed to run the application:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

For tokenizer, corpus, pre-training, fine-tuning, and evaluation instructions, see [docs/TRAINING.md](docs/TRAINING.md). For technical details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/OLLAMA.md](docs/OLLAMA.md), and [docs/DATA_AND_LICENSING.md](docs/DATA_AND_LICENSING.md).

### Project Structure

```text
assets/        User interface, styles, scripts, and logo
clara_core/    Server, Ollama runtime, agent, tools, and SQLite storage
scripts/       Corpus, tokenizer, and training utilities
docs/          Architecture, Ollama, data, and training documentation
tests/         Automated tests
avora-worker/  Optional worker
run.py         Local server entry point
```

The educational Transformer path can be selected with `AVORA_ENGINE=transformer`. The internal `clara_core` package name is retained for compatibility.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the release history and project updates.

---

## Contributing

Contributions, bug reports, and suggestions are welcome. Before submitting a change:

1. Clearly describe the issue or improvement.
2. Do not include private datasets, model checkpoints, credentials, confidential logs, or personal data.
3. Add tests for changes to the server, storage layer, or model-related components.
4. Run the test suite before opening a pull request.

---

## License

Avora's application code is distributed under the **MIT License**. See [LICENSE](./LICENSE) for the full license text.

Language models, voices, and external services are separate third-party components and remain subject to their respective licenses and terms of use.

---

## Contact & Support

- **Maintainer:** [@nowii-core](https://github.com/nowii-core)
- **Project:** part of the [nowii-core](https://github.com/nowii-core) ecosystem.
- **Issues and ideas:** use the Issues and Pull Requests tabs of the repository where you host Avora.

---

<div align="center">
  <sub>Developed by <b>nowii-core</b></sub>
</div>
