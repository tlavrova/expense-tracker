import { isMonth, shiftMonth, thisMonth, today } from './dates';

describe('dates', () => {
  it('today() uses the local date, padded', () => {
    expect(today(new Date(2026, 0, 5, 23, 30))).toBe('2026-01-05');
  });

  it('thisMonth() is today without the day', () => {
    expect(thisMonth(new Date(2026, 10, 30))).toBe('2026-11');
  });

  it('isMonth() accepts only real YYYY-MM months', () => {
    expect(['2026-11', '2026-01'].map(isMonth)).toEqual([true, true]);
    expect(['2026-13', '2026-1', 'november', '', undefined].map(isMonth)).toEqual([
      false,
      false,
      false,
      false,
      false,
    ]);
  });

  it('shiftMonth() moves across years', () => {
    expect(shiftMonth('2026-01', -1)).toBe('2025-12');
    expect(shiftMonth('2026-12', 1)).toBe('2027-01');
  });
});
