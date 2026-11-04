/**
 * Settings for `npm start` on your Mac. The deployed site (stage 13) gets its own version of this
 * file with the online API address.
 */
export const environment = {
  /** The FastAPI backend: `cd backend && uvicorn api:app --reload`. */
  apiUrl: 'http://localhost:8000',
};
