import { HttpErrorResponse } from '@angular/common/http';
import { environment } from '../../environments/environment';

/**
 * A sentence for the page from a failed API call.
 *
 * The backend always answers errors as {"detail": "a readable message"} (backend/api.py), so
 * that message is shown as it is. Status 0 means the browser couldn't reach the API at all.
 *
 * Online, the API runs on Render's free plan: it sleeps after 15 idle minutes and takes about a
 * minute to wake up. Meanwhile calls fail with status 0 or a 502/503/504 from Render's proxy
 * (without our {"detail"}), so the site says that instead of a developer hint.
 */
export function apiErrorMessage(error: unknown, production = environment.production): string {
  if (!(error instanceof HttpErrorResponse)) {
    return 'Something went wrong.';
  }
  const detail: unknown = error.error?.detail;
  if (typeof detail === 'string') {
    return detail;
  }
  if (production && (error.status === 0 || WAKING_UP_STATUSES.includes(error.status))) {
    return WAKING_UP;
  }
  if (error.status === 0) {
    return `Can't reach the API at ${environment.apiUrl}. Is it running? (cd backend && uvicorn api:app --reload)`;
  }
  return `The API answered with an error (${error.status}).`;
}

export const WAKING_UP =
  "The server isn't answering. It sleeps when nobody has used it for a while and takes about a minute to wake up, so please try again shortly.";

/** What Render's proxy answers while the API is starting (502 bad gateway, 503, 504 timeout). */
const WAKING_UP_STATUSES = [502, 503, 504];
