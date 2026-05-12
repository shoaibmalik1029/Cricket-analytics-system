const API_BASE = import.meta.env.VITE_API_BASE || "/api";

async function request(path) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`);
  } catch (error) {
    throw new Error("Unable to reach the Python API. Start FastAPI and keep it running while using the React app.");
  }
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || payload.error || detail;
    } catch (error) {
      // Ignore JSON parsing failures and fall back to HTTP status.
    }
    throw new Error(detail);
  }
  return response.json();
}

async function post(path, payload) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  } catch (error) {
    throw new Error("Unable to reach the Python API. Start FastAPI and keep it running while using the React app.");
  }
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || payload.error || detail;
    } catch (error) {
      // Ignore JSON parsing failures and fall back to HTTP status.
    }
    throw new Error(detail);
  }
  return response.json();
}

export const api = {
  health: () => request("/health"),
  meta: () => request("/meta"),
  dashboard: () => request("/dashboard"),
  saveScoredMatch: (payload) => post("/scorer/matches", payload),
  predictOptions: (format = "ODI") => request(`/predict/options?format=${encodeURIComponent(format)}`),
  predict: async (payload) => {
    let response;
    try {
      response = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } catch (error) {
      throw new Error("Unable to reach the Python API. Start FastAPI and keep it running while using the React app.");
    }
    if (!response.ok) {
      let detail = `Request failed: ${response.status}`;
      try {
        const payload = await response.json();
        detail = payload.detail || payload.error || detail;
      } catch (error) {
        // Ignore JSON parsing failures and fall back to HTTP status.
      }
      throw new Error(detail);
    }
    return response.json();
  },
  teams: ({ format = "All", query = "" } = {}) =>
    request(`/teams?format=${encodeURIComponent(format)}&query=${encodeURIComponent(query)}`),
  teamProfile: (teamName, format = "All") =>
    request(`/teams/${encodeURIComponent(teamName)}?format=${encodeURIComponent(format)}`),
  players: ({ format = "All", country = "All", query = "" } = {}) =>
    request(
      `/players?format=${encodeURIComponent(format)}&country=${encodeURIComponent(country)}&query=${encodeURIComponent(query)}`
    ),
  playerProfile: (playerName, format = "All") =>
    request(`/players/${encodeURIComponent(playerName)}?format=${encodeURIComponent(format)}`),
  headToHead: ({ format = "ODI", teamA, teamB }) =>
    request(
      `/analysis/head-to-head?format=${encodeURIComponent(format)}&team_a=${encodeURIComponent(teamA)}&team_b=${encodeURIComponent(teamB)}`
    ),
  teamForm: ({ format = "ODI", team, window = 8 }) =>
    request(`/analysis/team-form?format=${encodeURIComponent(format)}&team=${encodeURIComponent(team)}&window=${window}`),
  playerForm: ({ format = "ODI", player, window = 8 }) =>
    request(`/analysis/player-form?format=${encodeURIComponent(format)}&player=${encodeURIComponent(player)}&window=${window}`),
  playerComparison: ({ format = "All", playerA, playerB }) =>
    request(
      `/analysis/player-comparison?format=${encodeURIComponent(format)}&player_a=${encodeURIComponent(playerA)}&player_b=${encodeURIComponent(playerB)}`
    ),
  oppositionReport: ({ format = "ODI", team, opponent }) =>
    request(
      `/analysis/opposition-report?format=${encodeURIComponent(format)}&team=${encodeURIComponent(team)}&opponent=${encodeURIComponent(opponent)}`
    ),
  upsetDetector: ({ format = "ODI", teamA, teamB }) =>
    request(`/analysis/upset?format=${encodeURIComponent(format)}&team_a=${encodeURIComponent(teamA)}&team_b=${encodeURIComponent(teamB)}`),
  query: async (payload) => {
    let response;
    try {
      response = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } catch (error) {
      throw new Error("Unable to reach the Python API. Start FastAPI and keep it running while using the React app.");
    }
    if (!response.ok) {
      let detail = `Request failed: ${response.status}`;
      try {
        const payload = await response.json();
        detail = payload.detail || payload.error || detail;
      } catch (error) {
        // Ignore JSON parsing failures and fall back to HTTP status.
      }
      throw new Error(detail);
    }
    return response.json();
  }
};
