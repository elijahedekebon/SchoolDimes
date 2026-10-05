import { describe, expect, it } from "vitest";

import { compareMoney, formatUGX, isValidAmount, sumMoney, toCents } from "./money";

describe("money (no floating point)", () => {
  it("parses decimal strings to integer cents", () => {
    expect(toCents("5000.00")).toBe(500000n);
    expect(toCents("0.1")).toBe(10n);
    expect(toCents("-12.5")).toBe(-1250n);
    expect(toCents("abc")).toBeNull();
  });

  it("formats UGX with grouping and drops .00", () => {
    expect(formatUGX("15000.00")).toBe("UGX 15,000");
    expect(formatUGX("1500.50")).toBe("UGX 1,500.50");
    expect(formatUGX("-2000.00")).toBe("-UGX 2,000");
    expect(formatUGX(null)).toBe("—");
  });

  it("sums exactly where floats would drift", () => {
    expect(sumMoney(["0.10", "0.20"])).toBe("0.30");
    expect(sumMoney(["9999999999.99", "0.01"])).toBe("10000000000.00");
  });

  it("compares and validates", () => {
    expect(compareMoney("10.00", "9.99")).toBe(1);
    expect(isValidAmount("0")).toBe(false);
    expect(isValidAmount("100.555")).toBe(false);
    expect(isValidAmount("100.5")).toBe(true);
  });
});
