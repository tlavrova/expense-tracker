/**
 * Settings for the deployed site (`ng build`, production). It replaces environment.ts, so both
 * files must have the same fields.
 */
export const environment = {
  /** The FastAPI backend on Render (free plan: sleeps after 15 idle minutes, the first visit then takes about a minute). */
  apiUrl: 'https://expense-tracker-xbnh.onrender.com',
};
