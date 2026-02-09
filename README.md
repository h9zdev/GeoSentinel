# 🌍 GeoSentinel

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Linux](https://img.shields.io/badge/Linux-Tested-green?style=for-the-badge&logo=linux)](https://www.linux.org/)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen?style=for-the-badge)](https://github.com/h9zdev/GeoSentinel)
[![GeoSentinel](https://img.shields.io/badge/GeoSentinel-Active-red?style=for-the-badge)](https://github.com/h9zdev/GeoSentinel)

</div>

<p align="center">
  <img src="https://raw.githubusercontent.com/h9zdev/GeoSentinel/main/images/GeoSentinel.png" alt="GeoSentinel" />
</p>

**GeoSentinel** is a geospatial monitoring platform that tracks global movement in real time.

It aggregates ship and flight routes, live coordinates, and geodata into a unified system, providing clear geographic and geopolitical awareness for analysis, visualization, and decision-making.
. 🚀

🚀 **Visit the Blog:**  
👉 https://haybnz.web.app/blog

🚀 **Visit the Blog:**  
👉 https://varadaraj.online/


---

🔴 **NOTE**  
Stay updated with the latest **Geo Sentinel AI** releases and announcements.

👉 **Subscribe here:**  
https://docs.google.com/forms/d/e/1FAIpQLSe3qBh6r1orih2MkLf5DjdolX0jv5Abct02363lLxpXEute-Q/viewform

## 🌟 Features

-   🗺️ Access to GeoJSON data and surveillance grid tiles.
-   ✈️ Real-time flight data.
-   🚢 Live vessel tracking.
-   🛰️ Advanced aerial segmentation with YOLO.
-   🖼️ Image analysis for object and GPS metadata.
-   📰 Geopolitical news and sentiment analysis.
-   💹 Market data for commodities and cryptocurrencies.
-   🌐 Translation services.
-   🔒 TOR integration for enhanced privacy.
-   🤖 OLLAMA AI integration for local LLM processing.
-   🕵️‍♂️ **Darkweb Search**: Anonymous searching across multiple .onion engines via TOR integration.
-   🔍 **Advanced Web Scraper**: Multi-engine OSINT search with Google Dorking for social media platforms (Twitter, Reddit, Instagram, etc.).
-   🤖 **GeoSential AI**: Intelligent assistant for automated real-time tracking of flights and vessels with integrated OSINT.

### 🌍 Earth HTML Features
-   Interactive global map with real-time tracking
-   Advanced search capabilities (HEX, flight, vessel, coordinates)
-   TomTom Maps API integration for detailed mapping
-   Activity logging and user tracking
-   Responsive design for all devices
-   GPS metadata extraction from images
-   Real-time data visualization
-   Integrated GeoSential AI for automated tracking and analysis
-   Advanced web scanning with social media dorking capabilities

###    📦 Download and Move `geodata` Folder to Root Directory

### 🔗 Download Link
👉 [Download geodata folder](https://drive.proton.me/urls/RJB7K8HXTM#r7PnpGiVkg6P)

## 📝 Configuration

### API Keys Required
- **TomTom Maps API**: Add your key in `templates/earth.html` (line ~1850)
  ```javascript
  const tomtomApiKey = 'YOUR_TOMTOM_API_KEY';
  ```

- **Other APIs**: Add relevant API keys in `app.py`

---


# 🛰️ GeoSentinel Installation Guide



### Option 1: Clone directly
```bash
git clone https://github.com/h9zdev/GeoSentinel.git
```

### Option 2: Fork the repository
https://github.com/h9zdev/GeoSentinel/fork

Then clone your fork:
```bash
git clone https://github.com/<your-username>/GeoSentinel.git
```

---

## 📂 Navigate to Project Directory
```bash
cd GeoSentinel
```

---

## 🧩 Install Dependencies
```bash
pip install -r requirements.txt
```

(Optional but recommended)
```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

---

## ▶️ Run the Application
```bash
python app.py
```

---

## 🌐 Open in Browser

- Earth View  
  https://127.0.0.1:8000/earth

- News Dashboard
  https://127.0.0.1:8000/news

---

## 🔒 TOR Installation & Setup (Linux)

### Option 1: Install TOR from Package Manager
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tor torbrowser-launcher -y

# Fedora/RHEL
sudo dnf install tor torbrowser-launcher -y
```

### Option 2: Install TOR from Source
```bash
# Download TOR
cd /tmp
wget https://archive.torproject.org/tor-package-archive/tor-latest.tar.gz
tar -xzf tor-latest.tar.gz
cd tor-*

# Compile and install
./configure
make
sudo make install
```

### Start TOR Service
```bash
# Start TOR daemon
sudo systemctl start tor
sudo systemctl enable tor  # Enable on boot

# Or run manually
tor

# Verify TOR is running
curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip
```



## 🤖 OLLAMA Installation & Setup

### Installation Steps

#### Step 1: Download OLLAMA
```bash
# macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from
https://ollama.ai/download
```

#### Step 2: Verify Installation
```bash
ollama --version
```

#### Step 3: Pull a Model
```bash
# Pull Llama 2 model (7B parameters)
ollama pull llama2

# Or pull other models
ollama pull mistral      # Mistral model
ollama pull neural-chat  # Neural Chat model
ollama pull orca-mini    # Orca Mini model
```

#### Step 4: Run OLLAMA Server
```bash
# Start OLLAMA server (runs on localhost:11434)
ollama serve
```




## 🙏 API TO USE

-   [OpenStreetMap](https://www.openstreetmap.org/)
-   [ADSB.one](https://adsb.one/)
-   [AISstream.io](https://aisstream.io/)
-   [CoinGecko](https://www.coingecko.com/)
-   [NewsAPI](https://newsapi.org/)
-   [tomtom](https://developer.tomtom.com)

## 🗺️ Images of GeoSentinel UI
![GeoSentinel Screenshot](images/Screenshot%20From%202026-01-08%2001-01-15.png)
![GeoSentinel Screenshot](https://github.com/h9zdev/GeoSentinel/blob/main/images/Screenshot%20From%202026-01-18%2019-29-41.png)
![GeoSentinel Screenshot](images/Screenshot%20From%202026-01-08%2002-44-21.png)
![GeoSentinel Screenshot](images/Screenshot%20From%202026-01-16%2016-47-19.png)
![GeoSentinel Screenshot](images/Screenshot%20From%202026-01-16%2016-46-43.png)
![GeoSentinel Screenshot](images/Screenshot%20From%202026-01-16%2016-46-25.png)
![GeoSentinel Screenshot](images/Screenshot%20From%202026-01-09%2014-04-26.png)


## 📜 License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) License. See the [LICENSE](LICENSE) file for more details.

**Unauthorized use is strictly prohibited.**

📧 Contact: singularat@protn.me

## ☕ Support

Donate via Monero: `45PU6txuLxtFFcVP95qT2xXdg7eZzPsqFfbtZp5HTjLbPquDAugBKNSh1bJ76qmAWNGMBCKk4R1UCYqXxYwYfP2wTggZNhq`

## 👥 Contributors and Developers

[<img src="https://avatars.githubusercontent.com/u/67865621?s=64&v=4" width="64" height="64" alt="haybnzz">](https://github.com/h9zdev)  
[<img src="https://avatars.githubusercontent.com/u/180658853?s=64&v=4" width="64" height="64" alt="Steiynbrodt">](https://github.com/Steiynbrodt)  
[<img src="https://avatars.githubusercontent.com/u/220222050?v=4&size=64" width="64" height="64" alt="H9yzz">](https://github.com/H9yzz)  
[<img src="https://avatars.githubusercontent.com/u/108749445?s=64&size=64" width="64" height="64" alt="VaradScript">](https://github.com/VaradScript)  

## 👥 
 X9 CYBERNETICS


## Star History

<a href="https://www.star-history.com/#h9zdev/GeoSentinel&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=h9zdev/GeoSentinel&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=h9zdev/GeoSentinel&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=h9zdev/GeoSentinel&type=date&legend=top-left" />
 </picture>
</a>


If you use NeuroTumorNet in your research, please cite:
Made with ❤️ and lots of ☕️.

