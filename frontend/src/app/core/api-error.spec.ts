import { HttpErrorResponse } from '@angular/common/http';
import { WAKING_UP, apiErrorMessage } from './api-error';

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

  describe('on the website (production)', () => {
    it.each([0, 502, 503, 504])('says the server may be waking up (status %i)', (status) => {
      const error = new HttpErrorResponse({ status, error: '<html>' });
      expect(apiErrorMessage(error, true)).toBe(WAKING_UP);
    });

    it("still shows the backend's own message, e.g. a 503 when AI isn't available", () => {
      const error = new HttpErrorResponse({
        status: 503,
        error: { detail: 'GEMINI_API_KEY is not set.' },
      });
      expect(apiErrorMessage(error, true)).toBe('GEMINI_API_KEY is not set.');
    });

    it('never gives the developer hint', () => {
      expect(apiErrorMessage(new HttpErrorResponse({ status: 0 }), true)).not.toContain('uvicorn');
    });
  });

  it('handles errors that are not HTTP errors', () => {
    expect(apiErrorMessage(new Error('boom'))).toBe('Something went wrong.');
  });
});
