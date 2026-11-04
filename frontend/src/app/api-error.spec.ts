import { HttpErrorResponse } from '@angular/common/http';
import { apiErrorMessage } from './api-error';

describe('apiErrorMessage', () => {
  it("shows the backend's own message", () => {
    const error = new HttpErrorResponse({
      status: 422,
      error: { detail: 'Amount must be greater than zero, got 0.0.' },
    });
    expect(apiErrorMessage(error)).toBe('Amount must be greater than zero, got 0.0.');
  });

  it('explains when the API cannot be reached', () => {
    expect(apiErrorMessage(new HttpErrorResponse({ status: 0 }))).toContain("Can't reach the API");
  });

  it('falls back to the status code when there is no message', () => {
    expect(apiErrorMessage(new HttpErrorResponse({ status: 502, error: '<html>' }))).toBe(
      'The API answered with an error (502).',
    );
  });

  it('handles errors that are not HTTP errors', () => {
    expect(apiErrorMessage(new Error('boom'))).toBe('Something went wrong.');
  });
});
