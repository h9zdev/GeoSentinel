# 🌍 GeoSentinel

**GeoSentinel** is a geospatial monitoring platform that tracks global movement in real time.

It aggregates ship and flight routes, live coordinates, and geodata into a unified system, providing clear geographic and geopolitical awareness for analysis, visualization, and decision-making.
. 🚀

🚀 Visit: [hayvnz.web.app](https://hayvnz.web.app)

## 🌟 Features

-   🗺️ Access to GeoJSON data and surveillance grid tiles.
-   ✈️ Real-time flight data.
-   🚢 Live vessel tracking.
-   🛰️ Advanced aerial segmentation with YOLO.
-   🖼️ Image analysis for object and GPS metadata.
-   📰 Geopolitical news and sentiment analysis.
-   💹 Market data for commodities and cryptocurrencies.
-   🌐 Translation services.

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

## 🙏 Acknowledgements

-   [OpenStreetMap](https://www.openstreetmap.org/)
-   [ADSB.one](https://adsb.one/)
-   [AISstream.io](https://aisstream.io/)
-   [CoinGecko](https://www.coingecko.com/)
-   [NewsAPI](https://newsapi.org/)

## 🗺️ Images of GeoSentinel UI

## GeoSentinel Visual Overview

![GeoSentinel Screenshot](images/Screenshot%20From%202026-01-08%2001-01-15.png)
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




If you use NeuroTumorNet in your research, please cite:
Made with ❤️ and lots of ☕️.
