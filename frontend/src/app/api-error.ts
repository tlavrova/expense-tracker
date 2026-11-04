import { HttpErrorResponse } from '@angular/common/http';
import { environment } from '../environments/environment';

/**
 * A sentence for the page from a failed API call.
 *
 * The backend always answers errors as {"detail": "a readable message"} (backend/api.py), so
 * that message is shown as it is. Status 0 means the browser couldn't reach the API at all.
 */
export function apiErrorMessage(error: unknown): string {
  if (!(error instanceof HttpErrorResponse)) {
    return 'Something went wrong.';
  }
  if (error.status === 0) {
    return `Can't reach the API at ${environment.apiUrl}. Is it running? (cd backend && uvicorn api:app --reload)`;
  }
  const detail: unknown = error.error?.detail;
  return typeof detail === 'string' ? detail : `The API answered with an error (${error.status}).`;
}
