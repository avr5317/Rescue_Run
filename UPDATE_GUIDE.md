# Install the progress-tracker update

The ZIP contains the complete project under one `RescueRun/` folder. The project root is the folder containing `app/`, `frontend/`, and `requirements.txt`.

## Update your existing checkout

1. Extract the ZIP into a separate folder. Keep your original Git checkout.
2. Copy the changed/new files listed below into the matching paths in your checkout. If you have edited these files since uploading the source, merge the changes instead of overwriting your newer work.
3. Keep your existing `.env`, database credentials, Git history, and local environment in place. The package includes only a placeholder `.env.example`.
4. Restart the backend and frontend using your usual commands:

```bash
# Project root, in your activated Python environment
uvicorn app.main:app --reload --port 8000
```

```bash
# Separate terminal, project root
cd frontend
npm ci
npm run dev
```

## Files to copy

| Path | Purpose |
| --- | --- |
| `app/models.py` | Adds the on-the-way status and progress response fields. |
| `app/progress.py` | Formats public history and UTC timestamps; supports older records. |
| `app/routes/requests.py` | Saves status events, enforces helper transitions, and returns update times. |
| `frontend/src/App.jsx` | Refreshes lists after progress changes and keeps completed requests accessible. |
| `frontend/src/api/requests.js` | Adds the status-update API call. |
| `frontend/src/components/RequestCard.jsx` | Shows status and last-updated time. |
| `frontend/src/components/RequestModal.jsx` | Adds the tracker, actions, and detail refresh. |
| `frontend/src/components/RequestProgress.jsx` | Delivery stages, timestamps, and status history. |
| `frontend/src/components/StatusBadge.jsx` | Readable colored status labels. |
| `frontend/src/components/LastUpdated.jsx` | Relative time and exact-time tooltip. |
| `frontend/src/utils/requestProgress.js` | Shared status and date handling. |
| `frontend/src/components/Sidebar.jsx` | In-progress requests and collapsible delivered history. |
| `frontend/src/components/BottomSheet.jsx` | Keeps the alternate list component consistent. |
| `frontend/src/components/MapView.jsx` | Status/time in popups and selected in-transit markers. |
| `frontend/package.json` | Adds the frontend test command; runtime dependencies are unchanged. |
| `frontend/tests/requestProgress.test.js` | Tests labels, UTC conversion, and stage rendering data. |
| `tests/test_request_progress.py` | HTTP workflow, permissions, timestamps, retry, and conflict tests. |
| `requirements-dev.txt` | Test-only dependencies. |
| `README.md` | Feature documentation and test commands. |
| `.env.example` | Optional placeholder configuration for a fresh setup. |

## Behavior worth knowing

- Only the claiming browser/device gets delivery-action buttons. The backend checks the same device identity and expected state, including during concurrent updates.
- Public responses no longer expose the helper's device token. `claim` now contains its timestamp; use `is_claiming_helper` for ownership-sensitive UI.
- The existing `POST /requests/{id}/delivered` endpoint remains, but now requires the on-the-way stage first.
- Requests with no external funding gap start funded so they can be claimed immediately.
- Funding totals and request status are updated together using a conditional write. This prevents a simultaneous donation from resetting a helper's progress. Donation ledger insertion remains a separate write, as in the original demo; this is not a new payment-processing system.
- Priority recomputation writes `ranked_at` separately from activity's `updated_at`. Existing stored update times cannot be retroactively separated from historical ranking activity.
- Unknown legacy transition times stay unknown. No database migration or historical rewrite is performed.
- Keep using the browser/device that claimed a request. This update reuses the original device-token identity mechanism, not a new account system.

## Validation

See README for the backend tests, frontend tests, and production build commands. The tests do not call real AI providers or connect to Atlas.
