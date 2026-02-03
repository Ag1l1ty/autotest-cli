const { add } = require("./index");

describe("add", () => {
  test("adds two positive numbers", () => {
    expect(add(1, 2)).toBe(3);
  });

  test("adds negative numbers", () => {
    expect(add(-3, -7)).toBe(-10);
  });

  test("adds zero", () => {
    expect(add(5, 0)).toBe(5);
  });
});
