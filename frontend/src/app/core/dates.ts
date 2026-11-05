/** Dates as the API writes them: days as YYYY-MM-DD, months as YYYY-MM, in the user's own time zone. */

/** Today as YYYY-MM-DD in the user's own time zone (toISOString() would use UTC). */
export function today(now = new Date()): string {
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${now.getFullYear()}-${month}-${day}`;
}

/** This month as YYYY-MM. */
export function thisMonth(now = new Date()): string {
  return today(now).slice(0, 7);
}

/** True for a real month like "2026-11" (not "2026-13" or "november"). */
export function isMonth(value: string | null | undefined): value is string {
  return !!value && /^\d{4}-(0[1-9]|1[0-2])$/.test(value);
}

/** A month moved by some months: shiftMonth("2026-01", -1) is "2025-12". */
export function shiftMonth(month: string, by: number): string {
  const [year, number] = month.split('-').map(Number);
  const moved = new Date(year, number - 1 + by, 1);
  return `${moved.getFullYear()}-${String(moved.getMonth() + 1).padStart(2, '0')}`;
}
