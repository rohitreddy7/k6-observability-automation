
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = 'https://test-api.k6.io';

export const options = {
  scenarios: {
    api_load_test: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '15s', target: 10 },
        { duration: '30s', target: 10 },
        { duration: '15s', target: 0 },
      ],
      gracefulRampDown: '5s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const response = http.get(
    `${BASE_URL}/public/crocodiles/`,
    {
      tags: { name: 'GET /public/crocodiles' },
      timeout: '10s',
    }
  );

const statusPassed = check(response, {
  'status is 200': (r) => r.status === 200,
});

const jsonPassed = check(response, {
  'response is JSON': (r) =>
    !!r.headers['Content-Type'] &&
    r.headers['Content-Type'].includes('application/json'),
});

if (!statusPassed) {
  console.error(`HTTP status check failed: ${response.status}`);
}

if (!jsonPassed) {
  console.error(
    `Content-Type check failed: ${
      response.headers['Content-Type'] || 'missing'
    }`
  );
}

  sleep(1);
}

export function handleSummary(data) {
  return {
    'k6_results.json': JSON.stringify(data, null, 2),
  };
}
