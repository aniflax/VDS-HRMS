# VDS-HRMS
VDS Application with below functionalities
- Aiding in salary cycle
- Onboaring new Sevaks
- To mark and track attendance and leaves
- Maintaining Sevak's data
- Drafting new policies and updating existing policies related
- Timely scaling up Sevaks to Ashramites

## Local Network Access

To make the frontend and backend reachable from another device on your LAN, start them on all interfaces:

- Frontend: `npm run dev` from `frontend` already binds Vite to `0.0.0.0:5173`.
- Backend: run `python -m app.main` from `backend` or set `HOST=0.0.0.0` and `PORT=8000` before launching uvicorn.

If email verification or password reset links need to work from another device, set `FRONTEND_URL` in `backend/.env` to the LAN URL you actually use, such as `http://192.168.1.121:5173`.
