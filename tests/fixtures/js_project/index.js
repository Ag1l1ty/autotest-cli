/**
 * Simple JS module with arithmetic helpers and an async data fetcher.
 */

function add(a, b) {
  return a + b;
}

function multiply(a, b) {
  return a * b;
}

async function fetchData(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

module.exports = { add, multiply, fetchData };
