# Backend API Documentation (Django + DRF) — Chat + Med-AI + Prescriptions

This backend provides:
- User authentication (login/signup/OTP, profile, admin dashboard)
- Chat endpoint that forwards text/file input to a FastAPI AI service
- Prescription management (CRUD via DRF ViewSets)
- Saving AI-extracted prescription data after user confirmation

---

## Base URL

Development (example):
- `http://<your-django-host>:8000/`

> If you use a global prefix like `/api/` or `/api/v1/`, add it in front of every endpoint below.

---

## Authentication

### Auth Header (JWT)
All protected endpoints require:

- `Authorization: Bearer <access_token>`

### Content Types
- JSON requests: `Content-Type: application/json`
- File uploads: `multipart/form-data` (your client will set it automatically)

---

## Quick Start (Local)

### 1) Run Django
```bash
python manage.py migrate
python manage.py runserver 8000
```

### 2) Run FastAPI AI Service
Your Django backend calls FastAPI at:

- `AI_BASE_URL` (default): `http://localhost:8001`

Run FastAPI on port `8001` and ensure it is reachable.

---

## Module: Users (`/users/`)

> The exact prefix depends on how your root `urls.py` includes this app.  
> The endpoints below are relative to the users include path (e.g. `/users/...`).

### Registration & OTP
- `POST signup/` — Create account
- `POST otp/request/` — Request OTP
- `POST otp/verify/` — Verify OTP

### Authentication
- `POST login/` — Login (returns JWT tokens or access token)
- `POST logout/` — Logout
- `POST password/reset/` — Reset password

### Account
- `DELETE account/delete/` — Delete account
- `POST account/deactivate/` — Deactivate account (JWT required)

### Profile
- `GET profile/` — My profile (JWT required)
- `POST password/change/` — Change password (JWT required)

### Dashboard
- `GET dashboard/<date>/` — User dashboard (date path param)

### Admin
- `GET admin/profile/` — Admin profile (JWT + Admin role)
- `POST admin/password/change/` — Admin change password (JWT + Admin role)
- `GET admin/dashboard/` — Admin dashboard stats
- `GET admin/users/` — User management
- `GET admin/doctors/` — Doctor list
- `GET admin/pharmacists/` — Pharmacist list

---

## Module: Chat + AI (`/chatboat/`)

### Overview
A single endpoint supports both:
- Text messages (`content` JSON)
- File messages (`file` multipart) — image/pdf/audio

Django saves the user's message, forwards the input to FastAPI, then saves the assistant reply.

### 1) Send Text Message
**POST** `chatboat/messages/`  
Headers:
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

Body:
```json
{
  "content": "How many medicines are left?"
}
```

Response (key fields you will use in UI):
- `assistant_message` (the AI reply)
- `confirmation_needed` (if `true`, show a “Save?” confirmation dialog)
- `ai_data` (backend-ready prescription data when intent is `add_prescription`)

### 2) Send File (Image/PDF/Voice) — multipart
**POST** `chatboat/messages/`  
Headers:
- `Authorization: Bearer <token>`

Form-data:
- `file`: picked file (image/pdf/audio)

Notes:
- Frontend always uploads using field name: `file`
- Backend detects if the file is audio and forwards it to FastAPI as `audio`, otherwise as `file`

Response keys:
- `assistant_message`
- `confirmation_needed`
- `ai_data`

### 3) Get Chat History
**GET** `chatboat/messages/`  
Headers:
- `Authorization: Bearer <token>`

Returns:
- List of chat messages for the authenticated user (newest-first if implemented that way).

### UI Rule (Important)
- Do **not** send `content` and `file` together in one request.
- If `confirmation_needed === true`, show “Save?” UI.
- If user presses **Yes**, call the Save Prescription endpoint below using `ai_data`.

---

## Module: Prescriptions / Treatments (`/treatments/`)

> Your app uses a DRF router. The exact prefix depends on how your root `urls.py` includes this app.  
> The endpoints below assume the app is included at `/treatments/`.

### Router Endpoints
- `GET / POST treatments/prescription/` — List / Create prescriptions
- `GET / PUT / PATCH / DELETE treatments/prescription/<id>/` — Prescription details
- `GET / POST treatments/pharmacy/` — Pharmacy endpoints (as implemented)
- `GET / POST treatments/medicines/` — Medicines endpoints (as implemented)

### Save Prescription from AI (User presses YES)
**POST** `treatments/prescription/from-ai/`  
Headers:
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

Body:
```json
{
  "data": {
    "users": 1,
    "doctor": null,
    "patient": {
      "name": "Daniel",
      "age": 69,
      "sex": "Male"
    },
    "medicines": [
      {
        "name": "Rosuvastatin",
        "how_many_time": 1,
        "how_many_day": 60,
        "stock": 60
      }
    ]
  }
}
```

Response:
```json
{
  "success": true,
  "prescription_id": 123
}
```

Notes:
- `data.users` is ignored by backend; the authenticated user is always used.
- `how_many_time` may be present in AI output but can be ignored if the DB does not store it.
- Medicine timing fields (morning/afternoon/evening/night) may remain `null` unless you implement scheduling.

---

## Module: Doctors (`/doctors/`)

### Doctor Profiles (ViewSet)
- `GET / POST doctors/profile/`
- `GET / PUT / PATCH / DELETE doctors/profile/<id>/`

### Doctor Notes (nested)
- `GET / POST doctors/profile/<doctor_pk>/notes/`
- `GET / PUT / PATCH / DELETE doctors/profile/<doctor_pk>/notes/<pk>/`

---

## FastAPI AI Service (Reference)

Django communicates with FastAPI (example base URL):
- `http://localhost:8001`

### `/ai/chat` (FastAPI)
- Text mode: **query param** `text` (no JSON body)
- File mode: `multipart` field `file` (image/pdf)
- Voice mode: `multipart` field `audio` (wav/mp3 etc.)
- Reply key in response: `assistant_message`
- When a prescription is detected, structured backend-ready output is returned in `data`

Optional endpoints (if raw OCR/STT is needed):
- `POST /ocr/extract` → `{ "raw_text": "..." }`
- `POST /voice/stt` → `{ "text": "...", "language": "en" }`

---

## Common Troubleshooting

### 1) `WinError 10061` / Connection refused to `localhost:8001`
FastAPI is not running or not reachable.
- Start FastAPI on port `8001`
- Verify: `http://localhost:8001/health` (if available)

### 2) 401 Unauthorized
- Missing `Authorization: Bearer <token>`
- Token expired or invalid

### 3) Upload not received
- Ensure multipart key is exactly `file` in the client

---

## Contact / Maintainers
- Backend: Django + DRF
- AI service: FastAPI
- Client: Flutter

