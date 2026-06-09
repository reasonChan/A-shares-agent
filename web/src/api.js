const jsonHeaders = {
  'Content-Type': 'application/json',
};

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }
  return response.json();
}

export function fetchHealth() {
  return request('/api/health');
}

export function runJob(job, date) {
  return request(`/api/run/${job}`, {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify({ date }),
  });
}

export function runAll(date) {
  return request('/api/run-all', {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify({ date }),
  });
}

export function fetchReports() {
  return request('/api/reports');
}

export function fetchPremarketLatest() {
  return request('/api/premarket/latest');
}

export async function fetchReport(name) {
  const response = await fetch(`/api/reports/${encodeURIComponent(name)}`);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.text();
}

export function fetchMarketQuotes(symbols) {
  if (symbols && symbols.length > 0) {
    return request('/api/market/quotes', {
      method: 'POST',
      headers: jsonHeaders,
      body: JSON.stringify({ symbols }),
    });
  }
  return request('/api/market/quotes');
}

export function fetchStockPage({ page, pageSize, sort, asc }) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    sort,
    asc: String(asc),
  });
  return request(`/api/market/stocks?${params.toString()}`);
}
