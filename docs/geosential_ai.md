# 🤖 GeoSential AI Documentation

Welcome to the **GeoSential AI** manual! GeoSential AI is your high-tech Geospatial Intelligence (GEOINT) and OSINT assistant, designed to automate tracking and provide real-time global briefings. 🌍🛰️

## 🚀 Overview

GeoSential AI integrates real-time web data, map functionality, and semantic memory to assist in monitoring global activities. It can track flights, vessels, scan sectors for signals, and provide up-to-the-minute news and market data.

## ⚙️ Installation

To use GeoSential AI, ensure the following dependencies and services are set up:

1. **Python Dependencies**:
   ```bash
   pip install requests beautifulsoup4 duckduckgo_search chromadb sentence-transformers gTTS
   ```
2. **AI Engines**:
   - **Cloud**: Obtain a Hugging Face token and set `HF_TOKEN` in `app.py`.
   - **Local**: Install [Ollama](https://ollama.com/), pull the `phi` and `all-minilm` models:
     ```bash
     ollama pull phi
     ollama pull all-minilm
     ```
3. **Tor (Optional)**: Required for dark web search integration.

## 🛠️ How to Use

### 🖥️ Interface
You can interact with GeoSential AI directly through the **Earth View** dashboard in the GeoSentinel UI. Look for the AI chat panel to start a conversation.

### 🔌 API Endpoint
For developers, the AI is accessible via the following endpoint:
- **URL**: `/api/geosentialai/chat`
- **Method**: `POST`
- **Payload**:
```json
{
  "message": "Track flight UAE202",
  "web_search": true,
  "human_mode": false,
  "engine": "huggingface",
  "context": {}
}
```

## 📜 Commands & Tags

GeoSential AI can trigger specific actions in the UI by outputting special tags. These tags allow the AI to interact directly with the map:

| Command | Action |
| :--- | :--- |
| `[TRACK_FLIGHT: <icao>]` | ✈️ Zooms the map to a specific flight using its ICAO hex code. |
| `[TRACK_VESSEL: <mmsi>]` | 🚢 Zooms the map to a specific vessel using its MMSI number. |
| `[SHOW_WEATHER: <lat>, <lng>]` | 🌦️ Opens the meteorology/environment GUI for the specified coordinates. |
| `[SCAN_MAP: <lat>, <lng>]` | 📡 Zooms to coordinates and initiates a sector-wide signal scan. |

## 🔍 Search Integration

GeoSential AI is equipped with a powerful web search capability 🕵️‍♂️.
- **Auto-Trigger**: The AI automatically enables web search if your message contains keywords like *news, stock, price, market, update, latest,* or *happening*.
- **DuckDuckGo Integration**: It uses DuckDuckGo to pull real-time snippets from the web to ground its answers in current events.

## 🧠 Memory System

The AI uses **ChromaDB** to maintain a "Memory Stream" 🧠. It remembers previous interactions and can recall relevant context to provide more personalized and consistent assistance.

## ⚙️ AI Engines

You can choose between two processing engines:
1. **Cloud (Hugging Face)**: Uses `Llama-3.1-8B-Instruct` for high-performance reasoning (Default).
2. **Local (Ollama)**: Uses the `phi` model running locally on your machine for enhanced privacy and offline use.

---
*Stay informed, stay ahead with GeoSential AI. 🚀*
