# 🌌 Voyager Web App — High-Level Plan

## 🎯 Overview

Goal: Build a public-facing web app that calls official **NASA APIs** to track **Voyager 1 & 2**, display **current positions**, and showcase **historic mission images** — all without scraping.

---

## 🔭 Data Sources

| Type | Description | Source / API |
| ------ | -------------- | --------------- |
| **Position / Ephemeris** | Distance, velocity, coordinates | **JPL Horizons API** |
| **Mission Status** | Engineering & health updates | **NASA / JPL mission status pages** |
| **Images** | Historic flyby photos & press media | **NASA Image & Video Library API** |
| **Science Data / Archives** | Raw mission data | **Planetary Data System (PDS)** |

> 💡 Most NASA data is **public domain**, though attribution is encouraged.

---

## 🧭 Architecture

### Frontend (React / Next.js / Vue)

- Responsive UI (desktop + mobile)  
- User-friendly navigation
- Fetch data from backend APIs
- Display spacecraft positions, distances, and images  
- Integrate dynamic timelines and visualizations  
- Optional: 3-D orbit viewer (Three.js / Plotly)

### Backend (FastAPI / Flask / Node)

Acts as a **proxy + cache layer** to:

- Hide API keys  
- Normalize & format data  
- Reduce rate-limit risk  
- Cache frequent queries (Redis or in-memory)

### Hosting

- **Frontend:** Vercel or Netlify  
- **Backend:** Render, Heroku, or AWS App Runner  
- **Images/CDN:** AWS S3 or Cloudflare R2

---

## ⚙️ Data Handling

| Function | Method |
| ----------- | -------- |
| **Fetch current data** | Call JPL Horizons API or use `astroquery.jplhorizons` |
| **Fetch images** | `https://images-api.nasa.gov/search?q=voyager` |
| **Cache strategy** | Refresh every 15–60 minutes |
| **Ephemeris plotting** | Convert state vectors to x/y/z projection |
| **Telemetry** | Display only public data (no restricted feeds) |

---

## 🧩 API Highlights

### NASA Image & Video Library API

- Public — no key needed for basic search  
- JSON format (image titles, URLs, dates, descriptions)

### JPL Horizons

- Official source for position, distance, velocity  
- Supports plain text, CSV, and JSON output  
- Spacecraft IDs: Voyager 1 → `-31`  |  Voyager 2 → `-32`

### Planetary Data System (PDS)

- Archival Voyager 1 & 2 raw images  
- Public download endpoints

---

## 💡 Recommended Features

1. **Live Tracker** — current distance, velocity, light-time delay  
2. **Mission Timeline** — Launch → Planetary Flybys → Interstellar Crossing  
3. **Image Gallery** — curated thumbnails from NASA Image API  
4. **Telemetry Dashboard** — basic power, signal strength, subsystem status  
5. **“Where Are They Now” Section** — direction arrows showing 3-D trajectories  
6. **Attribution Footer** — “Data from NASA / JPL / PDS — Public Domain”

---

## ⚠️ Notes

- **No scraping needed** — NASA provides official APIs and archives  
- **Cache results** to avoid rate limits  
- **Respect CORS** — if APIs block browser calls, route through backend  
- **Data cadence** — Voyager telemetry updates are not real-time

---

## 🧰 Optional Extensions

- Compare Voyager data with Pioneer or New Horizons  
- Add educational overlays (light-time visualization, signal delay)  
- “Send a Message” simulation — show round-trip signal time

---

## 📅 Minimum Viable Product (MVP)

| Priority | Feature | Description |
| ----------- | ---------- | -------------- |
| ✅ | Live Distance Display | Real-time fetch from JPL Horizons |
| ✅ | Image Gallery | Pull from NASA Image API |
| ✅ | Timeline | Static dataset of key events |
| 🔜 | Caching Layer | Redis or memory cache for API results |
| 🔜 | 3-D Orbit Visualization | Optional for Phase 2 |
