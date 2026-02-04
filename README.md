# 🌍 GeoSentinel
<p align="center">
  <img src="https://raw.githubusercontent.com/h9zdev/GeoSentinel/main/images/GeoSentinel.png" alt="GeoSentinel" />
</p>


**GeoSentinel** is a geospatial monitoring platform that tracks global movement in real time.

It aggregates ship and flight routes, live coordinates, and geodata into a unified system, providing clear geographic and geopolitical awareness for analysis, visualization, and decision-making.
. 🚀

🚀 Visit Blog: [haybnz.web.app](https://haybnz.web.app/blog)

## 🌟 Features

-   🗺️ Access to GeoJSON data and surveillance grid tiles.
-   ✈️ Real-time flight data.
-   🚢 Live vessel tracking.
-   🛰️ Advanced aerial segmentation with YOLO.
-   🖼️ Image analysis for object and GPS metadata.
-   📰 Geopolitical news and sentiment analysis.
-   💹 Market data for commodities and cryptocurrencies.
-   🌐 Translation services.
-   
###    📦 Download and Move `geodata` Folder to Root Directory

### 🔗 Download Link
👉 [Download geodata folder](https://drive.proton.me/urls/RJB7K8HXTM#r7PnpGiVkg6P)

### 🔗 Download Link
-ADD API KEY IN app.py
-ADD API KEY IN earth.html {on line1850 const tomtomApiKey = 'ADD_API+KEY';}

# 🛰️ GeoSentinel Installation Guide

## 📥 Clone or Fork the Repository

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

## ✅ Notes
- SSL warnings are normal for localhost with HTTPS.
- Use http://127.0.0.1:8000 if HTTPS is not configured.
## ⚙️ API Endpoints

### 🌎 Earth

-   **GET /earth**
    -   Renders the main earth page.

### 🗺️ GeoJSON

-   **GET /api/geojson/<filename>**
    -   Retrieves a summary of a GeoJSON file.
    -   Example: `/api/geojson/example.geojson`

### 🛰️ Surveillance Grid

-   **GET /api/geo/index**
    -   Retrieves the surveillance grid index.
-   **GET /api/geo/tile/<z>/<x>/<y>**
    -   Retrieves a specific surveillance grid tile.
    -   Example: `/api/geo/tile/1/2/3`

### ✈️ Flights

-   **GET /api/geo/flights**
    -   Fetches live flight data.
-   **GET /api/geo/flight/meta/<callsign>**
    -   Retrieves metadata for a specific flight.
    -   Example: `/api/geo/flight/meta/UAL123`

### 🚢 Vessels

-   **GET /api/geo/vessels**
    -   Fetches live vessel data.
-   **GET /api/geo/vessel/path/<mmsi>**
    -   Retrieves the historical path of a vessel.
    -   Example: `/api/geo/vessel/path/123456789`

### 📸 Image Analysis

-   **POST /api/geo/segment**
    -   Performs aerial segmentation on a satellite tile.
-   **POST /api/geo/analyze-upload** or **/upload**
    -   Analyzes an uploaded image for objects and GPS metadata.

### 📰 News

-   **GET /api/geo/news**
    -   Fetches geopolitical news for a specific location.
-   **POST /api/news/analyze**
    -   Analyzes the sentiment of a news article.
-   **GET /api/news/advanced**
    -   Performs an advanced search for news articles.

### 💹 Market

-   **GET /api/market/data**
    -   Fetches market data for commodities and cryptocurrencies.

### 🌐 Translate

-   **GET /api/translate**
    -   Translates text to English.

## 🚀 How to Use


```bash
curl http://localhost:8000/api/geo/flights
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

