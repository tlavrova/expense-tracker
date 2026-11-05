/**
 * Settings for `npm start` on your Mac. `ng build` (production) uses environment.prod.ts instead.
 */
export const environment = {
  /** false: error messages may give developer hints (start the API with uvicorn). */
  production: false,
  /** The FastAPI backend: `cd backend && uvicorn api:app --reload`. */
  apiUrl: 'http://localhost:8000',
};
