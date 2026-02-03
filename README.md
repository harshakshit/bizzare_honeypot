# 🍯 LLM Honeypot: Operation "Bizarre Bazaar" Replication

![Status](https://img.shields.io/badge/Status-Live-success) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green)

A low-interaction honeypot designed to detect and log "LLMjacking" attacks—campaigns that scan for exposed AI infrastructure to steal compute resources for commercial resale.

This project specifically replicates the signatures of **Ollama**, **vLLM**, and **MCP** services to attract the "Validator" bots described in [Pillar Security's "Operation Bizarre Bazaar" research](https://www.pillar.security/blog/operation-bizarre-bazaar-first-attributed-llmjacking-campaign-with-commercial-marketplace-monetization).

## 🏗️ Architecture

The honeypot consists of a single `FastAPI` application that binds to multiple ports, mimicking specific AI service fingerprints.

| Service | Port | Signature Mimicked | Behavior |
| :--- | :--- | :--- | :--- |
| **Ollama** | `11434` | `/api/tags`, `/api/generate` | Returns fake model list (`llama3`, `mistral`) and generic chat responses. |
| **vLLM** | `8000` | `/v1/models`, `/v1/chat/completions` | Mimics OpenAI-compatible API endpoints used by vLLM. |
| **MCP** | `3000` | Generic JSON RPC | Catches IoT/Web scanners and Model Context Protocol probes. |



## 🚨 Key Findings (Live Data)

Within **45 minutes** of deployment on a public cloud instance, the node was identified and targeted.

### 1. Confirmed "LLMjacking" Validators 🔴
We captured automated bots matching the *Bizarre Bazaar* campaign signature.
* **Behavior:** Scanned `/v1/models` to list available LLMs.
* **Payload:** Sent `POST` requests with basic prompts (e.g., `{"content": "hi"}`) to verify if the server provides free inference.
* **Target Models:** Specifically probed for `meta-llama/Llama-2-7b-chat-hf` and `gpt-3.5-turbo`.

### 2. RCE Exploitation Attempts ⚫
Attackers attempted to exploit the web layer using **NodeJS Prototype Pollution** payloads, trying to inject a reverse shell (`/bin/sh`) connecting back to a command-and-control server.

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* `pip`
* A public IP (cloud VPS recommended for actual logging)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/harshakshit/bizzare_honeypot.git
    cd llm-honeypot
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Usage (Manual)

To run the honeypot manually for testing:

```bash
# Run the Ollama profile
HONEYPOT_PROFILE=ollama uvicorn honeypot:app --host 0.0.0.0 --port 11434

# Run the vLLM profile
HONEYPOT_PROFILE=vllm uvicorn honeypot:app --host 0.0.0.0 --port 8000
