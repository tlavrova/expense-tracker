/**
 * Settings for the deployed site (`ng build`, production). It replaces environment.ts, so both
 * files must have the same fields.
 */
export const environment = {
  /** The hosted FastAPI backend. Set once the backend host is chosen (stage 13). */
  apiUrl: 'https://expense-tracker-api.example.invalid',
};
