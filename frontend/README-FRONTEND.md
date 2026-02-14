# Crisis Mutual Aid – Frontend

Uber-style crisis mutual-aid web app: full-screen map, ranked requests bottom sheet, create request (AI intake), donate, and helper delivery flow.

## Tech stack

- **React 18** + **Vite 5**
- **Leaflet** (react-leaflet) for maps; dark OSM tiles
- **Tailwind CSS** for styling (glassmorphism, dark theme)
- **Axios** for API calls with `X-Device-Token` header
- **Framer Motion** for bottom sheet and animations

## Setup

```bash
npm install
```

## Run

Backend must be running at `http://localhost:8000` (e.g. `uvicorn app.main:app --reload --port 8000`).

```bash
npm run dev
```

App: **http://localhost:5173**

Optional: `cp .env.example .env` and set `VITE_API_URL` if your API is not at `http://localhost:8000/v1`.

## Features

- **Device token**: `POST /v1/device` on first load; token stored in `localStorage` and sent as `X-Device-Token` on all requests.
- **Map**: Full-viewport Leaflet map; fetches `GET /v1/requests?bbox=...&status=open&sort=rank` on bounds change; category-colored markers (meds=red, groceries=green, shelter=blue, transport=purple); click marker → Request detail modal.
- **Bottom sheet**: Ranked request cards with category icon, urgency (NOW/TODAY/WEEK), progress bar, funding left, rank score; poll every 5s.
- **Create request**: FAB “Request Help” → modal with textarea → `POST /v1/ai/invoke` → show AI draft → user enters “how much I can afford” → `POST /v1/requests`.
- **Donate**: In request modal, preset $5 / $10 / $25 or custom → `POST /v1/requests/{id}/donate`; progress bar animates.
- **Deliver**: When `status === "funded"`, “Deliver” → `POST /v1/requests/{id}/claim`; then “Open in Google Maps” link with destination lat,lng.
- **Demo**: Top banner “Ranked by urgency and vulnerability, not profit.” Crisis Mode toggle and vulnerability badges (Elderly, Infant, Disabled) for narrative/judging.

## Project structure

```
src/
  api/axios.js       # Axios instance, device token header
  api/device.js      # ensureDeviceToken()
  api/requests.js    # fetchRequests, fetchRequestDetail, createRequest, donate, claim, invokeAI
  components/
    MapView.jsx
    BottomSheet.jsx
    RequestCard.jsx
    RequestModal.jsx
    CreateRequestModal.jsx
    FloatingButtons.jsx
  App.jsx
  main.jsx
  index.css
```
