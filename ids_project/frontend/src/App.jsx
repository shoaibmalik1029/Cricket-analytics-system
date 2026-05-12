import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

const navItems = [
  { key: "dashboard", label: "Dashboard" },
  { key: "scorer", label: "Scorer" },
  { key: "predict", label: "Predictions" },
  { key: "intelligence", label: "Intelligence" },
  { key: "players", label: "Players" },
  { key: "teams", label: "Teams" },
  { key: "settings", label: "Settings" }
];

const DISMISSAL_TYPES = [
  { value: "bowled", label: "Bowled" },
  { value: "caught", label: "Caught" },
  { value: "lbw", label: "LBW" },
  { value: "run out", label: "Run out" },
  { value: "stumped", label: "Stumped" },
  { value: "hit wicket", label: "Hit wicket" },
  { value: "obstructing the field", label: "Obstructing field" },
  { value: "hit the ball twice", label: "Hit ball twice" },
  { value: "retired out", label: "Retired out" }
];

const FREE_HIT_DISMISSALS = new Set(["run out", "obstructing the field", "hit the ball twice"]);
const NO_BALL_DISMISSALS = new Set(["run out", "obstructing the field", "hit the ball twice"]);
const BOWLER_WICKET_TYPES = new Set(["bowled", "caught", "lbw", "stumped", "hit wicket"]);

const defaultScorerState = {
  teamA: "Team A",
  teamB: "Team B",
  battingTeam: "Team A",
  bowlingTeam: "Team B",
  format: "ODI",
  maxOvers: 50,
  ground: "Local Ground",
  matchDate: new Date().toISOString().slice(0, 10),
  inningsNumber: 1,
  striker: "Batter 1",
  nonStriker: "Batter 2",
  bowler: "Bowler 1",
  totalRuns: 0,
  wickets: 0,
  legalBalls: 0,
  target: "",
  freeHitNext: false,
  matchComplete: false,
  innings: [],
  batters: {
    "Batter 1": { runs: 0, balls: 0, fours: 0, sixes: 0, out: false },
    "Batter 2": { runs: 0, balls: 0, fours: 0, sixes: 0, out: false }
  },
  bowlers: {
    "Bowler 1": { balls: 0, runs: 0, wickets: 0, maidens: 0 }
  },
  pendingChanges: [],
  events: [],
  history: []
};

function loadSavedScorerState() {
  try {
    const saved = localStorage.getItem("elite-cricket-scorer");
    return saved ? normalizeScorerState({ ...defaultScorerState, ...JSON.parse(saved) }) : defaultScorerState;
  } catch (error) {
    return defaultScorerState;
  }
}

function App() {
  const [page, setPage] = useState("dashboard");
  const [scorerState, setScorerState] = useState(loadSavedScorerState);
  const [backendReady, setBackendReady] = useState(false);
  const [bootMessage, setBootMessage] = useState("Starting Python analytics engine...");
  const [meta, setMeta] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [playerFormat, setPlayerFormat] = useState("ODI");
  const [playerCountry, setPlayerCountry] = useState("All");
  const [playerQuery, setPlayerQuery] = useState("");
  const [playerList, setPlayerList] = useState([]);
  const [playerCountries, setPlayerCountries] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState("");
  const [playerProfile, setPlayerProfile] = useState(null);
  const [teamFormat, setTeamFormat] = useState("ODI");
  const [teamQuery, setTeamQuery] = useState("");
  const [teamList, setTeamList] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState("");
  const [teamProfile, setTeamProfile] = useState(null);
  const [predictFormat, setPredictFormat] = useState("ODI");
  const [predictOptions, setPredictOptions] = useState({ formats: [], teams: [], venue_modes: [] });
  const [predictForm, setPredictForm] = useState({
    format: "ODI",
    team_a: "",
    team_b: "",
    venue_mode: "Neutral",
    year: new Date().getFullYear()
  });
  const [predictionResult, setPredictionResult] = useState(null);
  const [intelFormat, setIntelFormat] = useState("ODI");
  const [intelTeams, setIntelTeams] = useState([]);
  const [intelPlayers, setIntelPlayers] = useState([]);
  const [intelTeamA, setIntelTeamA] = useState("");
  const [intelTeamB, setIntelTeamB] = useState("");
  const [intelPlayerA, setIntelPlayerA] = useState("");
  const [intelPlayerB, setIntelPlayerB] = useState("");
  const [headToHead, setHeadToHead] = useState(null);
  const [teamFormInsight, setTeamFormInsight] = useState(null);
  const [playerFormInsight, setPlayerFormInsight] = useState(null);
  const [playerComparison, setPlayerComparison] = useState(null);
  const [oppositionReport, setOppositionReport] = useState(null);
  const [upsetInsight, setUpsetInsight] = useState(null);
  const [queryText, setQueryText] = useState("Predict India vs Australia");
  const [queryResult, setQueryResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    let timerId;

    async function boot() {
      setError("");
      try {
        setBootMessage("Checking Python API...");
        await api.health();
        setBootMessage("Loading dataset and ML model...");
        const [metaData, dashboardData] = await Promise.all([api.meta(), api.dashboard()]);
        if (cancelled) return;
        setMeta(metaData);
        setDashboard(dashboardData);
        setBackendReady(true);
        setBootMessage("");
      } catch (err) {
        if (cancelled) return;
        setBackendReady(false);
        setBootMessage("Backend is still warming up. Retrying automatically...");
        timerId = setTimeout(boot, 3000);
      }
    }

    boot();
    return () => {
      cancelled = true;
      if (timerId) clearTimeout(timerId);
    };
  }, []);

  useEffect(() => {
    localStorage.setItem("elite-cricket-scorer", JSON.stringify(scorerState));
  }, [scorerState]);

  useEffect(() => {
    if (backendReady) loadPlayers();
  }, [backendReady, playerFormat, playerCountry]);

  useEffect(() => {
    if (backendReady) loadTeams();
  }, [backendReady, teamFormat]);

  useEffect(() => {
    if (!backendReady) return;
    api.predictOptions(predictFormat).then((data) => {
      setPredictOptions(data);
      setPredictForm((current) => ({
        ...current,
        format: predictFormat,
        team_a: current.team_a || data.teams?.[0] || "",
        team_b: current.team_b && current.team_b !== current.team_a ? current.team_b : data.teams?.[1] || data.teams?.[0] || "",
        venue_mode: current.venue_mode || data.venue_modes?.[0] || "Neutral"
      }));
    }).catch((err) => setError(err.message));
  }, [backendReady, predictFormat]);

  useEffect(() => {
    if (!backendReady || !meta?.formats?.length) return;
    Promise.all([
      api.predictOptions(intelFormat),
      api.players({ format: intelFormat, country: "All", query: "" })
    ])
      .then(([teamData, playerData]) => {
        setIntelTeams(teamData.teams || []);
        setIntelPlayers((playerData.items || []).map((item) => item.player));
        setIntelTeamA((current) => current || teamData.teams?.[0] || "");
        setIntelTeamB((current) => current || teamData.teams?.[1] || teamData.teams?.[0] || "");
        setIntelPlayerA((current) => current || playerData.items?.[0]?.player || "");
        setIntelPlayerB((current) => current || playerData.items?.[1]?.player || playerData.items?.[0]?.player || "");
      })
      .catch((err) => setError(err.message));
  }, [backendReady, meta, intelFormat]);

  useEffect(() => {
    if (backendReady && selectedPlayer) {
      api.playerProfile(selectedPlayer, playerFormat).then(setPlayerProfile).catch((err) => setError(err.message));
    }
  }, [backendReady, selectedPlayer, playerFormat]);

  useEffect(() => {
    if (backendReady && selectedTeam) {
      api.teamProfile(selectedTeam, teamFormat).then(setTeamProfile).catch((err) => setError(err.message));
    }
  }, [backendReady, selectedTeam, teamFormat]);

  async function loadPlayers(query = playerQuery) {
    setLoading(true);
    setError("");
    try {
      const data = await api.players({ format: playerFormat, country: playerCountry, query });
      setPlayerList(data.items);
      setPlayerCountries(["All", ...data.countries.filter((country, index, arr) => arr.indexOf(country) === index)]);
      if (data.items.length && !data.items.some((item) => item.player === selectedPlayer)) {
        setSelectedPlayer(data.items[0].player);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadTeams(query = teamQuery) {
    setLoading(true);
    setError("");
    try {
      const data = await api.teams({ format: teamFormat, query });
      setTeamList(data.items);
      if (data.items.length && !data.items.some((item) => item.country === selectedTeam)) {
        setSelectedTeam(data.items[0].country);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleScoredMatchSaved() {
    setLoading(true);
    setError("");
    try {
      const [metaData, dashboardData] = await Promise.all([api.meta(), api.dashboard()]);
      setMeta(metaData);
      setDashboard(dashboardData);
      await Promise.all([loadPlayers(), loadTeams()]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const pageTitle = useMemo(() => navItems.find((item) => item.key === page)?.label || "Dashboard", [page]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">C</div>
          <div>
            <h1>Elite Cricket</h1>
            <p>Professional Suite</p>
          </div>
        </div>

        <nav className="nav">
          {navItems.map((item) => (
            <button key={item.key} className={`nav-item ${page === item.key ? "active" : ""}`} onClick={() => setPage(item.key)}>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-status">
          <span>System Status</span>
          <strong>{backendReady ? "Cloud Sync Active" : "Warming Up Backend"}</strong>
          <p>{meta ? `${meta.total_players} players loaded` : bootMessage || "Loading dataset..."}</p>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <h2>{pageTitle}</h2>
            <p>{meta ? `${meta.formats.join(", ")} • ${meta.date_range}` : bootMessage || "Connecting to API..."}</p>
          </div>
          <input className="global-search" placeholder="Search analytics..." />
        </header>

        {error ? <div className="banner error">{error}</div> : null}
        {!backendReady ? <div className="banner">{bootMessage}</div> : null}
        {loading ? <div className="banner">Loading latest analytics...</div> : null}

        <section className="page-scroll">
          {page === "dashboard" && <DashboardPage meta={meta} dashboard={dashboard} />}
          {page === "scorer" && <ScorerPage scorerState={scorerState} setScorerState={setScorerState} onMatchSaved={handleScoredMatchSaved} />}
          {page === "predict" && (
            <PredictPage
              predictFormat={predictFormat}
              setPredictFormat={setPredictFormat}
              predictOptions={predictOptions}
              predictForm={predictForm}
              setPredictForm={setPredictForm}
              predictionResult={predictionResult}
              onPredict={async () => {
                setLoading(true);
                setError("");
                try {
                  const result = await api.predict(predictForm);
                  if (result.error) {
                    setError(result.error);
                    return;
                  }
                  setPredictionResult(result);
                } catch (err) {
                  setError(err.message);
                } finally {
                  setLoading(false);
                }
              }}
            />
          )}
          {page === "intelligence" && (
            <IntelligencePage
              intelFormat={intelFormat}
              setIntelFormat={setIntelFormat}
              formats={meta?.formats || []}
              intelTeams={intelTeams}
              intelPlayers={intelPlayers}
              intelTeamA={intelTeamA}
              setIntelTeamA={setIntelTeamA}
              intelTeamB={intelTeamB}
              setIntelTeamB={setIntelTeamB}
              intelPlayerA={intelPlayerA}
              setIntelPlayerA={setIntelPlayerA}
              intelPlayerB={intelPlayerB}
              setIntelPlayerB={setIntelPlayerB}
              headToHead={headToHead}
              teamFormInsight={teamFormInsight}
              playerFormInsight={playerFormInsight}
              playerComparison={playerComparison}
              oppositionReport={oppositionReport}
              upsetInsight={upsetInsight}
              queryText={queryText}
              setQueryText={setQueryText}
              queryResult={queryResult}
              onRunHeadToHead={async () => {
                setLoading(true);
                setError("");
                try {
                  const [h2h, form, report, upset] = await Promise.all([
                    api.headToHead({ format: intelFormat, teamA: intelTeamA, teamB: intelTeamB }),
                    api.teamForm({ format: intelFormat, team: intelTeamA, window: 8 }),
                    api.oppositionReport({ format: intelFormat, team: intelTeamA, opponent: intelTeamB }),
                    api.upsetDetector({ format: intelFormat, teamA: intelTeamA, teamB: intelTeamB })
                  ]);
                  if (h2h.error || form.error || report.error || upset.error) {
                    setError(h2h.error || form.error || report.error || upset.error);
                    return;
                  }
                  setHeadToHead(h2h);
                  setTeamFormInsight(form);
                  setOppositionReport(report);
                  setUpsetInsight(upset);
                } catch (err) {
                  setError(err.message);
                } finally {
                  setLoading(false);
                }
              }}
              onRunComparison={async () => {
                setLoading(true);
                setError("");
                try {
                  const [comparison, form] = await Promise.all([
                    api.playerComparison({ format: intelFormat, playerA: intelPlayerA, playerB: intelPlayerB }),
                    api.playerForm({ format: intelFormat, player: intelPlayerA, window: 8 })
                  ]);
                  if (comparison.error || form.error) {
                    setError(comparison.error || form.error);
                    return;
                  }
                  setPlayerComparison(comparison);
                  setPlayerFormInsight(form);
                } catch (err) {
                  setError(err.message);
                } finally {
                  setLoading(false);
                }
              }}
              onRunQuery={async () => {
                setLoading(true);
                setError("");
                try {
                  const result = await api.query({ query: queryText, format: intelFormat });
                  setQueryResult(result);
                } catch (err) {
                  setError(err.message);
                } finally {
                  setLoading(false);
                }
              }}
            />
          )}
          {page === "players" && (
            <PlayersPage
              meta={meta}
              playerFormat={playerFormat}
              setPlayerFormat={setPlayerFormat}
              playerCountry={playerCountry}
              setPlayerCountry={setPlayerCountry}
              playerCountries={playerCountries}
              playerQuery={playerQuery}
              setPlayerQuery={setPlayerQuery}
              playerList={playerList}
              selectedPlayer={selectedPlayer}
              setSelectedPlayer={setSelectedPlayer}
              playerProfile={playerProfile}
              onSearch={() => loadPlayers()}
            />
          )}
          {page === "teams" && (
            <TeamsPage
              meta={meta}
              teamFormat={teamFormat}
              setTeamFormat={setTeamFormat}
              teamQuery={teamQuery}
              setTeamQuery={setTeamQuery}
              teamList={teamList}
              selectedTeam={selectedTeam}
              setSelectedTeam={setSelectedTeam}
              teamProfile={teamProfile}
              onSearch={() => loadTeams()}
            />
          )}
          {page === "settings" && <SettingsPage />}
        </section>
      </main>
    </div>
  );
}

function DashboardPage({ meta, dashboard }) {
  const summaryCards = [
    { label: "Formats", value: meta?.formats?.join(", ") || "--" },
    { label: "Players", value: meta?.total_players || "--" },
    { label: "Teams", value: meta?.total_teams || "--" },
    { label: "Date Range", value: meta?.date_range || "--" }
  ];

  return (
    <div className="content-grid dashboard-grid">
      <div className="kpi-row">
        {summaryCards.map((card) => (
          <article className="card kpi-card" key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </article>
        ))}
      </div>

      <article className="card hero-card">
        <div>
          <p className="eyebrow">Live Now</p>
          <h3>International match intelligence hub</h3>
          <p>FastAPI serves player, team, and format analytics to React over HTTP. This screen is now frontend-ready instead of bound to Tkinter.</p>
          {dashboard?.prediction_sample ? (
            <div className="prediction-inline">
              <span>ML Sample</span>
              <strong>{dashboard.prediction_sample.winner}</strong>
              <p>
                {dashboard.prediction_sample.team_a} win chance {dashboard.prediction_sample.team_a_win_probability}% vs{" "}
                {dashboard.prediction_sample.team_b}
              </p>
            </div>
          ) : null}
        </div>
      </article>

      <article className="card side-card">
        <h3>Top Teams</h3>
        <ListTable rows={dashboard?.top_teams || []} columns={["country", "format", "win_rate"]} />
      </article>

      <article className="card wide-card">
        <h3>Top Batters</h3>
        <ListTable rows={dashboard?.top_batters || []} columns={["player", "country", "format", "runs", "batting_average", "strike_rate"]} />
      </article>

      <article className="card side-card">
        <h3>Top Bowlers</h3>
        <ListTable rows={dashboard?.top_bowlers || []} columns={["player", "country", "format", "wickets", "economy_rate"]} />
      </article>
    </div>
  );
}

function PredictPage({ predictFormat, setPredictFormat, predictOptions, predictForm, setPredictForm, predictionResult, onPredict }) {
  const minYear = predictOptions.min_year || 1877;
  const maxYear = predictOptions.max_year || new Date().getFullYear();
  return (
    <div className="content-grid predict-grid">
      <article className="card filters-card">
        <div className="filter-row">
          <select value={predictFormat} onChange={(e) => setPredictFormat(e.target.value)}>
            {(predictOptions.formats?.length ? predictOptions.formats : ["ODI", "T20I", "Test"]).map((format) => (
              <option key={format}>{format}</option>
            ))}
          </select>
          <select
            value={predictForm.team_a}
            onChange={(e) => setPredictForm((current) => ({ ...current, team_a: e.target.value }))}
          >
            {predictOptions.teams?.map((team) => (
              <option key={`a-${team}`} value={team}>
                {team}
              </option>
            ))}
          </select>
          <select
            value={predictForm.team_b}
            onChange={(e) => setPredictForm((current) => ({ ...current, team_b: e.target.value }))}
          >
            {predictOptions.teams?.map((team) => (
              <option key={`b-${team}`} value={team}>
                {team}
              </option>
            ))}
          </select>
          <select
            value={predictForm.venue_mode}
            onChange={(e) => setPredictForm((current) => ({ ...current, venue_mode: e.target.value }))}
          >
            {(predictOptions.venue_modes?.length ? predictOptions.venue_modes : ["Home", "Away", "Neutral"]).map((mode) => (
              <option key={mode}>{mode}</option>
            ))}
          </select>
          <input
            type="number"
            value={predictForm.year}
            onChange={(e) => setPredictForm((current) => ({ ...current, year: Number(e.target.value) }))}
            placeholder="Year"
            min={minYear}
            max={maxYear}
          />
          <button onClick={onPredict}>Run Prediction</button>
        </div>
      </article>

      <article className="card hero-card">
        <p className="eyebrow">ML Match Prediction</p>
        <h3>{predictionResult?.winner || "Select teams and run the model"}</h3>
        <p>
          This prediction is generated from historical international results plus team batting and bowling strength features from the loaded dataset.
        </p>
        <div className="stats-grid">
          <Stat label={`${predictForm.team_a || "Team A"} Win %`} value={predictionResult?.team_a_win_probability} />
          <Stat label={`${predictForm.team_b || "Team B"} Win %`} value={predictionResult?.team_b_win_probability} />
          <Stat label="Head-to-Head A %" value={predictionResult?.head_to_head_team_a} />
        </div>
      </article>

      <article className="card">
        <h3>{predictForm.team_a || "Team A"} Strength</h3>
        <ListTable
          rows={predictionResult?.team_a_strength ? [predictionResult.team_a_strength] : []}
          columns={["win_rate", "batting_average", "batting_runs_per_over", "bowling_average", "bowling_runs_per_over"]}
        />
      </article>

      <article className="card">
        <h3>{predictForm.team_b || "Team B"} Strength</h3>
        <ListTable
          rows={predictionResult?.team_b_strength ? [predictionResult.team_b_strength] : []}
          columns={["win_rate", "batting_average", "batting_runs_per_over", "bowling_average", "bowling_runs_per_over"]}
        />
      </article>
    </div>
  );
}

function ScorerPage({ scorerState, setScorerState, onMatchSaved }) {
  const score = `${scorerState.totalRuns}/${scorerState.wickets}`;
  const overs = formatOvers(scorerState.legalBalls);
  const currentRunRate = scorerState.legalBalls ? ((scorerState.totalRuns * 6) / scorerState.legalBalls).toFixed(2) : "0.00";
  const target = Number(scorerState.target);
  const hasTarget = target && scorerState.inningsNumber > 1 && !scorerState.matchComplete;
  const runsNeeded = hasTarget ? Math.max(target - scorerState.totalRuns, 0) : null;
  const maxBalls = Number(scorerState.maxOvers) > 0 ? Number(scorerState.maxOvers) * 6 : null;
  const inningsComplete = scorerState.matchComplete || scorerState.wickets >= 10 || (maxBalls !== null && scorerState.legalBalls >= maxBalls) || (hasTarget && scorerState.totalRuns >= target);
  const currentBatter = scorerState.batters[scorerState.striker] || emptyBatter();
  const currentBowler = scorerState.bowlers[scorerState.bowler] || emptyBowler();
  const pendingChanges = scorerState.pendingChanges || [];
  const currentPending = pendingChanges[0] || null;
  const baseCanScore = !currentPending && !inningsComplete;
  const [pendingName, setPendingName] = useState("");
  const [dismissalType, setDismissalType] = useState("bowled");
  const [fielderName, setFielderName] = useState("");
  const [saveStatus, setSaveStatus] = useState("");
  const pendingNameError = getPendingNameError(pendingName, currentPending, scorerState);
  const isFreeHit = Boolean(scorerState.freeHitNext);
  const needsFielder = dismissalNeedsFielder(dismissalType);
  const matchResult = getMatchResult(scorerState);
  const bowlerQuotaError = getBowlerQuotaError(scorerState.bowler, scorerState);
  const canScore = baseCanScore && !bowlerQuotaError;

  useEffect(() => {
    setPendingName(currentPending?.suggestedName || "");
  }, [currentPending?.id, currentPending?.suggestedName]);

  function updateField(field, value) {
    setScorerState((current) => {
      const next = { ...current, [field]: value };
      if (field === "teamA" && current.battingTeam === current.teamA) next.battingTeam = value;
      if (field === "teamA" && current.bowlingTeam === current.teamA) next.bowlingTeam = value;
      if (field === "teamB" && current.battingTeam === current.teamB) next.battingTeam = value;
      if (field === "teamB" && current.bowlingTeam === current.teamB) next.bowlingTeam = value;
      if (field === "battingTeam") next.bowlingTeam = value === current.teamA ? current.teamB : current.teamA;
      if (field === "format" && current.maxOvers === defaultOversForFormat(current.format)) next.maxOvers = defaultOversForFormat(value);
      return next;
    });
  }

  function updateParticipant(field, value) {
    setScorerState((current) => {
      const next = { ...current, [field]: value };
      if (field === "striker" || field === "nonStriker") {
        next.batters = { ...current.batters, [value]: current.batters[value] || emptyBatter() };
      }
      if (field === "bowler") {
        next.bowlers = { ...current.bowlers, [value]: current.bowlers[value] || emptyBowler() };
      }
      return next;
    });
  }

  function swapStrike() {
    setScorerState((current) => ({ ...current, striker: current.nonStriker, nonStriker: current.striker }));
  }

  function addBall({ runs = 0, extra = 0, extraType = "", wicket = false, legal = true, dismissal = "", fielder = "" }) {
    setScorerState((current) => {
      if ((current.pendingChanges || []).length || current.wickets >= 10 || current.matchComplete || getBowlerQuotaError(current.bowler, current)) {
        return current;
      }
      const batters = { ...current.batters };
      const bowlers = { ...current.bowlers };
      const striker = batters[current.striker] || emptyBatter();
      const bowler = bowlers[current.bowler] || emptyBowler();
      const freeHitActive = Boolean(current.freeHitNext);
      const validWicket = wicket && isDismissalAllowed({ dismissal, extraType, freeHitActive });
      const dismissalText = validWicket ? formatDismissal({ dismissal, fielder, bowler: current.bowler }) : "";
      const batterRuns = extraType === "bye" || extraType === "leg bye" || extraType === "wide" ? 0 : runs;
      const bowlerRuns = extraType === "bye" || extraType === "leg bye" ? 0 : runs + extra;
      const nextLegalBalls = current.legalBalls + (legal ? 1 : 0);
      const nextWickets = current.wickets + (validWicket ? 1 : 0);
      const totalForBall = runs + extra;
      const currentMaxBalls = Number(current.maxOvers) > 0 ? Number(current.maxOvers) * 6 : null;
      const nextTotal = current.totalRuns + totalForBall;
      const nextInningsComplete =
        nextWickets >= 10 ||
        (currentMaxBalls !== null && nextLegalBalls >= currentMaxBalls) ||
        (Number(current.target) && current.inningsNumber > 1 && nextTotal >= Number(current.target));
      const nextMatchComplete = isLimitedOvers(current.format) && current.inningsNumber >= 2 && nextInningsComplete;
      const deliveryLabel = `${formatOvers(nextLegalBalls - (legal ? 0 : 1))}${legal ? "" : "*"}${freeHitActive ? " FH" : ""}`;

      batters[current.striker] = {
        ...striker,
        runs: striker.runs + batterRuns,
        balls: striker.balls + (legal ? 1 : 0),
        fours: striker.fours + (batterRuns === 4 ? 1 : 0),
        sixes: striker.sixes + (batterRuns === 6 ? 1 : 0),
        out: validWicket ? true : striker.out,
        dismissal: validWicket ? dismissalText : striker.dismissal,
        dismissalType: validWicket ? dismissal : striker.dismissalType,
        fielder: validWicket ? fielder : striker.fielder
      };

      bowlers[current.bowler] = {
        ...bowler,
        balls: bowler.balls + (legal ? 1 : 0),
        runs: bowler.runs + bowlerRuns,
        wickets: bowler.wickets + (countsForBowler(dismissal) && validWicket ? 1 : 0)
      };

      const event = {
        id: Date.now(),
        over: deliveryLabel,
        batter: current.striker,
        bowler: current.bowler,
        runs,
        extra,
        extraType,
        wicket: validWicket ? dismissalText : wicket ? "Not out on free hit/no-ball" : "",
        dismissalType: validWicket ? dismissal : "",
        fielder: validWicket ? fielder : "",
        legal,
        freeHit: freeHitActive ? "yes" : "",
        scoreAfter: `${current.totalRuns + totalForBall}/${nextWickets}`
      };

      let nextStriker = current.striker;
      let nextNonStriker = current.nonStriker;
      const crossedOddRuns = totalForBall % 2 === 1 && extraType !== "wide";
      if (!validWicket && legal && crossedOddRuns) {
        nextStriker = current.nonStriker;
        nextNonStriker = current.striker;
      }
      if (!validWicket && !legal && crossedOddRuns) {
        nextStriker = current.nonStriker;
        nextNonStriker = current.striker;
      }
      if (legal && nextLegalBalls % 6 === 0) {
        [nextStriker, nextNonStriker] = [nextNonStriker, nextStriker];
      }
      const nextPendingChanges = [];
      if (validWicket && nextWickets < 10 && !nextInningsComplete) {
        nextPendingChanges.push({
          id: `${event.id}-batter`,
          type: "batter",
          replace: "striker",
          title: "New batter required",
          message: `${current.striker} is out. Enter the next batter before scoring another ball.`,
          suggestedName: `Batter ${Object.keys(batters).length + 1}`
        });
      }
      if (legal && nextLegalBalls % 6 === 0 && nextWickets < 10 && !nextInningsComplete) {
        nextPendingChanges.push({
          id: `${event.id}-bowler`,
          type: "bowler",
          title: "New bowler required",
          message: `Over ${Math.floor(nextLegalBalls / 6)} is complete. Enter the bowler for the next over.`,
          suggestedName: `Bowler ${Object.keys(bowlers).length + 1}`
        });
      }
      const nextFreeHit = extraType === "no ball" || (freeHitActive && !legal);

      const nextState = {
        ...current,
        totalRuns: nextTotal,
        wickets: nextWickets,
        legalBalls: nextLegalBalls,
        freeHitNext: nextFreeHit,
        matchComplete: nextMatchComplete,
        striker: nextStriker,
        nonStriker: nextNonStriker,
        batters,
        bowlers,
        pendingChanges: nextPendingChanges,
        events: [event, ...current.events].slice(0, 120),
        history: [...(current.history || []), snapshotScorerState(current)].slice(-120)
      };
      if (nextMatchComplete) {
        nextState.pendingChanges = [];
        nextState.target = "";
        nextState.innings = [...(current.innings || []), inningsSnapshot(nextState)];
      }
      return nextState;
    });
  }

  function applyPendingChange() {
    const name = pendingName.trim();
    if (!currentPending || !name || pendingNameError) return;
    setScorerState((current) => {
      const [pending, ...remaining] = current.pendingChanges || [];
      if (!pending) return current;
      if (getPendingNameError(name, pending, current)) return current;
      if (pending.type === "batter") {
        return {
          ...current,
          [pending.replace]: name,
          batters: { ...current.batters, [name]: current.batters[name] || emptyBatter() },
          pendingChanges: remaining
        };
      }
      if (pending.type === "bowler") {
        return {
          ...current,
          bowler: name,
          bowlers: { ...current.bowlers, [name]: current.bowlers[name] || emptyBowler() },
          pendingChanges: remaining
        };
      }
      return { ...current, pendingChanges: remaining };
    });
  }

  function undoLastBall() {
    setScorerState((current) => {
      const history = current.history || [];
      const previous = history[history.length - 1];
      if (!previous) return current;
      return { ...previous, history: history.slice(0, -1) };
    });
  }

  function resetInnings() {
    setScorerState((current) => {
      const innings = [...(current.innings || []), inningsSnapshot(current)];
      if (isLimitedOvers(current.format) && current.inningsNumber >= 2) {
        return {
          ...current,
          innings,
          pendingChanges: [],
          matchComplete: true,
          target: "",
          history: [...(current.history || []), snapshotScorerState(current)].slice(-120)
        };
      }
      return {
        ...defaultScorerState,
        teamA: current.teamA,
        teamB: current.teamB,
        battingTeam: current.bowlingTeam,
        bowlingTeam: current.battingTeam,
        format: current.format,
        maxOvers: current.maxOvers,
        ground: current.ground,
        matchDate: current.matchDate,
        inningsNumber: current.inningsNumber + 1,
        target: current.totalRuns + 1,
        innings,
        events: [],
        history: []
      };
    });
  }

  function resetMatch() {
    setScorerState({ ...defaultScorerState });
  }

  async function saveMatch() {
    setSaveStatus("Saving scored match...");
    try {
      const payload = {
        ...scorerState,
        innings: scorerState.matchComplete ? scorerState.innings || [] : [...(scorerState.innings || []), inningsSnapshot(scorerState)]
      };
      const result = await api.saveScoredMatch(payload);
      setSaveStatus(`Saved ${result.player_rows} player rows and ${result.team_rows} team rows into the final dataset.`);
      if (onMatchSaved) await onMatchSaved();
    } catch (error) {
      setSaveStatus(error.message);
    }
  }

  return (
    <div className="content-grid scorer-grid">
      <article className="card scorer-scoreboard wide-card">
        <div>
          <p className="eyebrow">{scorerState.battingTeam} batting</p>
          <h3>{score}</h3>
          <p>
            Overs {overs} - CRR {currentRunRate}
            {runsNeeded !== null ? ` - Need ${runsNeeded} to win` : ""}
            {scorerState.matchComplete ? ` - ${matchResult}` : ""}
          </p>
        </div>
        <div className="scoreboard-pair">
          <Stat label="Striker" value={`${scorerState.striker} ${currentBatter.runs} (${currentBatter.balls})`} />
          <Stat label="Bowler" value={`${scorerState.bowler} ${formatOvers(currentBowler.balls)}-${currentBowler.runs}-${currentBowler.wickets}`} />
        </div>
      </article>

      <article className="card filters-card wide-card">
        <div className="filter-row">
          <input value={scorerState.teamA} onChange={(e) => updateField("teamA", e.target.value)} placeholder="Team A" />
          <input value={scorerState.teamB} onChange={(e) => updateField("teamB", e.target.value)} placeholder="Team B" />
          <select value={scorerState.format} onChange={(e) => updateField("format", e.target.value)}>
            {["ODI", "T20I", "Test"].map((format) => <option key={format}>{format}</option>)}
          </select>
          <input value={scorerState.maxOvers} onChange={(e) => updateField("maxOvers", e.target.value)} placeholder="Max overs" type="number" min="1" />
          <select value={scorerState.battingTeam} onChange={(e) => updateField("battingTeam", e.target.value)}>
            {[scorerState.teamA, scorerState.teamB].map((team) => <option key={team}>{team}</option>)}
          </select>
          <input value={scorerState.ground} onChange={(e) => updateField("ground", e.target.value)} placeholder="Ground" />
          <input value={scorerState.matchDate} onChange={(e) => updateField("matchDate", e.target.value)} type="date" />
          {scorerState.inningsNumber > 1 && !scorerState.matchComplete ? (
            <input value={scorerState.target} onChange={(e) => updateField("target", e.target.value)} placeholder="Target" type="number" min="1" />
          ) : null}
        </div>
        <div className="filter-row">
          <input value={scorerState.striker} onChange={(e) => updateParticipant("striker", e.target.value)} placeholder="Striker" />
          <input value={scorerState.nonStriker} onChange={(e) => updateParticipant("nonStriker", e.target.value)} placeholder="Non-striker" />
          <input value={scorerState.bowler} onChange={(e) => updateParticipant("bowler", e.target.value)} placeholder="Bowler" />
          <button onClick={swapStrike} disabled={Boolean(currentPending)}>Swap Strike</button>
        </div>
      </article>

      {currentPending ? (
        <article className="card scorer-prompt wide-card">
          <div>
            <p className="eyebrow">{currentPending.type === "bowler" ? "Over complete" : "Wicket"}</p>
            <h3>{currentPending.title}</h3>
            <p>{currentPending.message}</p>
          </div>
          <div className="filter-row">
            <input
              value={pendingName}
              onChange={(e) => setPendingName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") applyPendingChange();
              }}
              placeholder={currentPending.type === "bowler" ? "Next bowler name" : "Next batter name"}
              autoFocus
            />
            <button onClick={applyPendingChange} disabled={!pendingName.trim() || Boolean(pendingNameError)}>
              Confirm
            </button>
          </div>
          {pendingNameError ? <p className="scorer-note">{pendingNameError}</p> : null}
        </article>
      ) : null}

      <article className="card">
        <h3>Ball Scoring</h3>
        {isFreeHit ? <p className="scorer-note">Free hit: only run out, obstructing the field, or hit the ball twice can dismiss the striker.</p> : null}
        {bowlerQuotaError ? <p className="scorer-note">{bowlerQuotaError}</p> : null}
        <div className="scoring-pad">
          {[0, 1, 2, 3, 4, 6].map((runs) => (
            <button key={runs} onClick={() => addBall({ runs })} disabled={!canScore}>{runs}</button>
          ))}
          <button onClick={() => addBall({ runs: 0, extra: 1, extraType: "wide", legal: false })} disabled={!canScore}>Wide</button>
          <button onClick={() => addBall({ runs: 1, extra: 1, extraType: "wide", legal: false })} disabled={!canScore}>Wide +1</button>
          <button onClick={() => addBall({ runs: 0, extra: 1, extraType: "no ball", legal: false })} disabled={!canScore}>No Ball</button>
          <button onClick={() => addBall({ runs: 1, extra: 1, extraType: "no ball", legal: false })} disabled={!canScore}>NB +1</button>
          <button onClick={() => addBall({ runs: 4, extra: 1, extraType: "no ball", legal: false })} disabled={!canScore}>NB +4</button>
          <button onClick={() => addBall({ runs: 6, extra: 1, extraType: "no ball", legal: false })} disabled={!canScore}>NB +6</button>
          <button onClick={() => addBall({ runs: 1, extra: 0, extraType: "bye" })} disabled={!canScore}>Bye 1</button>
          <button onClick={() => addBall({ runs: 1, extra: 0, extraType: "leg bye" })} disabled={!canScore}>Leg Bye 1</button>
          <select value={dismissalType} onChange={(e) => setDismissalType(e.target.value)} disabled={!canScore}>
            {DISMISSAL_TYPES.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
          </select>
          {needsFielder ? (
            <input value={fielderName} onChange={(e) => setFielderName(e.target.value)} placeholder={dismissalType === "caught" ? "Catcher name" : "Fielder name"} disabled={!canScore} />
          ) : null}
          <button
            className="danger-button"
            onClick={() => addBall({ runs: 0, wicket: true, dismissal: dismissalType, fielder: fielderName.trim() })}
            disabled={!canScore || (needsFielder && !fielderName.trim())}
          >
            Wicket
          </button>
          <button onClick={undoLastBall} disabled={!scorerState.events.length}>Undo</button>
        </div>
        {inningsComplete ? <p className="scorer-note">Innings complete. End the innings or save the match data.</p> : null}
        <div className="filter-row scorer-actions">
          <button onClick={resetInnings} disabled={scorerState.matchComplete}>{isLimitedOvers(scorerState.format) && scorerState.inningsNumber >= 2 ? "End Match" : "End Innings"}</button>
          <button onClick={saveMatch}>Save Match Data</button>
          <button onClick={resetMatch}>New Match</button>
        </div>
        {saveStatus ? <p className="scorer-note">{saveStatus}</p> : null}
      </article>

      <article className="card">
        <h3>Batting Card</h3>
        <ListTable rows={scorecardRows(scorerState)} columns={["player", "runs", "balls", "fours", "sixes", "strike_rate", "status"]} />
      </article>

      <article className="card">
        <h3>Bowling Card</h3>
        <ListTable rows={bowlingRows(scorerState.bowlers)} columns={["bowler", "overs", "runs", "wickets", "economy"]} />
      </article>

      <article className="card">
        <h3>Ball Log</h3>
        <ListTable rows={scorerState.events} columns={["over", "batter", "bowler", "runs", "extra", "extraType", "freeHit", "fielder", "wicket", "scoreAfter"]} />
      </article>
    </div>
  );
}

function PlayersPage(props) {
  const {
    meta,
    playerFormat,
    setPlayerFormat,
    playerCountry,
    setPlayerCountry,
    playerCountries,
    playerQuery,
    setPlayerQuery,
    playerList,
    selectedPlayer,
    setSelectedPlayer,
    playerProfile,
    onSearch
  } = props;

  return (
    <div className="content-grid players-grid">
      <article className="card filters-card">
        <div className="filter-row">
          <select value={playerFormat} onChange={(e) => setPlayerFormat(e.target.value)}>
            {["All", ...(meta?.formats || [])].map((format) => (
              <option key={format}>{format}</option>
            ))}
          </select>
          <select value={playerCountry} onChange={(e) => setPlayerCountry(e.target.value)}>
            {playerCountries.map((country) => (
              <option key={country}>{country}</option>
            ))}
          </select>
          <input value={playerQuery} onChange={(e) => setPlayerQuery(e.target.value)} placeholder="Search player name" />
          <button onClick={onSearch}>Search</button>
        </div>
        <div className="filter-row">
          <select value={selectedPlayer} onChange={(e) => setSelectedPlayer(e.target.value)}>
            {playerList.map((player) => (
              <option key={`${player.player}-${player.country}`} value={player.player}>
                {player.player} [{player.country}]
              </option>
            ))}
          </select>
        </div>
      </article>

      <article className="card player-hero">
        <p className="eyebrow">{playerProfile?.profile?.country || "--"} • {playerProfile?.profile?.format || "--"}</p>
        <h3>{playerProfile?.profile?.player || "Select a player"}</h3>
        <p>{playerProfile?.profile?.role || "Role unavailable"}</p>
        <div className="stats-grid">
          <Stat label="Runs" value={playerProfile?.profile?.runs} />
          <Stat label="Bat Avg" value={playerProfile?.profile?.batting_average} />
          <Stat label="SR" value={playerProfile?.profile?.strike_rate} />
          <Stat label="Wickets" value={playerProfile?.profile?.wickets} />
          <Stat label="Bowl Avg" value={playerProfile?.profile?.bowling_average} />
          <Stat label="Economy" value={playerProfile?.profile?.economy_rate} />
        </div>
      </article>

      <article className="card">
        <h3>Career by Format</h3>
        <ListTable rows={playerProfile?.career_by_format || []} columns={["format", "runs", "wickets", "batting_average", "strike_rate", "economy_rate"]} />
      </article>

      <article className="card">
        <h3>Against Opponents</h3>
        <ListTable rows={playerProfile?.against || []} columns={["opposition", "runs", "wickets", "batting_average", "strike_rate"]} />
      </article>

      <article className="card wide-card">
        <h3>Recent Innings</h3>
        <ListTable rows={playerProfile?.recent || []} columns={["date", "opposition", "ground", "runs", "balls_faced", "batting_strike_rate", "wickets"]} />
      </article>
    </div>
  );
}

function IntelligencePage(props) {
  const {
    intelFormat,
    setIntelFormat,
    formats,
    intelTeams,
    intelPlayers,
    intelTeamA,
    setIntelTeamA,
    intelTeamB,
    setIntelTeamB,
    intelPlayerA,
    setIntelPlayerA,
    intelPlayerB,
    setIntelPlayerB,
    headToHead,
    teamFormInsight,
    playerFormInsight,
    playerComparison,
    oppositionReport,
    upsetInsight,
    queryText,
    setQueryText,
    queryResult,
    onRunHeadToHead,
    onRunComparison,
    onRunQuery
  } = props;

  return (
    <div className="content-grid intelligence-grid">
      <article className="card hero-card wide-card">
        <p className="eyebrow">Advanced Intelligence</p>
        <h3>Matchup, form, scouting, and natural-language analysis</h3>
        <p>This layer adds richer demo-ready functionality on top of the existing match predictor using the same historical engine and dataset.</p>
      </article>

      <article className="card filters-card wide-card">
        <div className="filter-row">
          <select value={intelFormat} onChange={(e) => setIntelFormat(e.target.value)}>
            {formats.map((format) => (
              <option key={format}>{format}</option>
            ))}
          </select>
          <select value={intelTeamA} onChange={(e) => setIntelTeamA(e.target.value)}>
            {intelTeams.map((team) => (
              <option key={`ia-${team}`} value={team}>
                {team}
              </option>
            ))}
          </select>
          <select value={intelTeamB} onChange={(e) => setIntelTeamB(e.target.value)}>
            {intelTeams.map((team) => (
              <option key={`ib-${team}`} value={team}>
                {team}
              </option>
            ))}
          </select>
          <button onClick={onRunHeadToHead}>Run Matchup Intelligence</button>
        </div>
        <div className="filter-row">
          <select value={intelPlayerA} onChange={(e) => setIntelPlayerA(e.target.value)}>
            {intelPlayers.map((player) => (
              <option key={`pa-${player}`} value={player}>
                {player}
              </option>
            ))}
          </select>
          <select value={intelPlayerB} onChange={(e) => setIntelPlayerB(e.target.value)}>
            {intelPlayers.map((player) => (
              <option key={`pb-${player}`} value={player}>
                {player}
              </option>
            ))}
          </select>
          <button onClick={onRunComparison}>Compare Players</button>
        </div>
        <div className="filter-row">
          <input value={queryText} onChange={(e) => setQueryText(e.target.value)} placeholder="Ask: Predict India vs Australia" />
          <button onClick={onRunQuery}>Run Query</button>
        </div>
      </article>

      <article className="card">
        <h3>Head-to-Head Predictor</h3>
        <div className="stats-grid">
          <Stat label="Matches" value={headToHead?.matches} />
          <Stat label={`${intelTeamA || "Team A"} Wins`} value={headToHead?.team_a_wins} />
          <Stat label={`${intelTeamB || "Team B"} Wins`} value={headToHead?.team_b_wins} />
          <Stat label={`${intelTeamA || "Team A"} Win Rate`} value={headToHead?.team_a_win_rate} />
          <Stat label="Recent Edge" value={headToHead?.psychological_edge} />
          <Stat label="Model Winner" value={headToHead?.model_prediction?.winner} />
        </div>
      </article>

      <article className="card">
        <h3>Upset Detector</h3>
        <div className="stats-grid">
          <Stat label="Favorite" value={upsetInsight?.favorite} />
          <Stat label="Underdog" value={upsetInsight?.underdog} />
          <Stat label="Favorite Win %" value={upsetInsight?.favorite_win_probability} />
          <Stat label="Upset %" value={upsetInsight?.upset_probability} />
        </div>
        <p>{upsetInsight?.reason || "Run matchup intelligence to assess upset potential."}</p>
      </article>

      <article className="card">
        <h3>Team Form Analyzer</h3>
        <div className="stats-grid">
          <Stat label="Win Rate" value={teamFormInsight?.win_rate} />
          <Stat label="Momentum" value={teamFormInsight?.momentum_score} />
          <Stat label="Volatility" value={teamFormInsight?.volatility_index} />
          <Stat label="Streak" value={teamFormInsight?.current_streak} />
        </div>
        <ListTable rows={teamFormInsight?.recent_matches || []} columns={["date", "opponent", "performance_label", "margin", "home_away"]} />
      </article>

      <article className="card">
        <h3>Player Comparison Tool</h3>
        <ListTable rows={playerComparison?.comparison || []} columns={["metric", "player_a", "player_b", "leader"]} />
      </article>

      <article className="card">
        <h3>Player Form Snapshot</h3>
        <div className="stats-grid">
          <Stat label="Avg Runs" value={playerFormInsight?.average_runs} />
          <Stat label="Avg Wickets" value={playerFormInsight?.average_wickets} />
          <Stat label="Avg Impact" value={playerFormInsight?.average_impact} />
          <Stat label="Volatility" value={playerFormInsight?.volatility_index} />
        </div>
      </article>

      <article className="card wide-card">
        <h3>Opposition Analysis Report</h3>
        <p>{oppositionReport?.vulnerabilities?.join(" ") || "Run matchup intelligence to generate scouting notes."}</p>
        <div className="dual-grid">
          <div>
            <h4>Threat Batters</h4>
            <ListTable rows={oppositionReport?.threat_batters || []} columns={["player", "innings", "runs", "average_runs"]} />
          </div>
          <div>
            <h4>Threat Bowlers</h4>
            <ListTable rows={oppositionReport?.threat_bowlers || []} columns={["player", "innings", "wickets", "economy_rate"]} />
          </div>
        </div>
      </article>

      <article className="card wide-card">
        <h3>Natural Language Query Interface</h3>
        <p>{queryResult?.message || "Ask for predictions, player comparisons, or team form in plain English."}</p>
        <JsonPreview data={queryResult?.answer} />
      </article>
    </div>
  );
}

function TeamsPage(props) {
  const { meta, teamFormat, setTeamFormat, teamQuery, setTeamQuery, teamList, selectedTeam, setSelectedTeam, teamProfile, onSearch } = props;
  return (
    <div className="content-grid teams-grid">
      <article className="card filters-card">
        <div className="filter-row">
          <select value={teamFormat} onChange={(e) => setTeamFormat(e.target.value)}>
            {["All", ...(meta?.formats || [])].map((format) => (
              <option key={format}>{format}</option>
            ))}
          </select>
          <input value={teamQuery} onChange={(e) => setTeamQuery(e.target.value)} placeholder="Search team name" />
          <button onClick={onSearch}>Search</button>
        </div>
        <div className="filter-row">
          <select value={selectedTeam} onChange={(e) => setSelectedTeam(e.target.value)}>
            {teamList.map((team) => (
              <option key={`${team.country}-${team.format}`} value={team.country}>
                {team.country} [{team.format}]
              </option>
            ))}
          </select>
        </div>
      </article>

      <article className="card">
        <h3>Team Profile</h3>
        <ListTable rows={teamProfile?.profile || []} columns={["format", "matches_played", "wins", "losses", "win_rate", "batting_average", "bowling_average"]} />
      </article>

      <article className="card">
        <h3>Against Opponents</h3>
        <ListTable rows={teamProfile?.against || []} columns={["opponent", "matches", "wins", "losses", "win_rate"]} />
      </article>

      <article className="card">
        <h3>Top Batters</h3>
        <ListTable rows={teamProfile?.top_batters || []} columns={["player", "runs", "batting_average", "strike_rate"]} />
      </article>

      <article className="card">
        <h3>Top Bowlers</h3>
        <ListTable rows={teamProfile?.top_bowlers || []} columns={["player", "wickets", "bowling_average", "economy_rate"]} />
      </article>

      <article className="card wide-card">
        <h3>Recent Results</h3>
        <ListTable rows={teamProfile?.recent || []} columns={["date", "opponent", "result", "margin", "home_away", "ground"]} />
      </article>
    </div>
  );
}

function SettingsPage() {
  return (
    <div className="content-grid settings-grid">
      <article className="card hero-card">
        <p className="eyebrow">Architecture</p>
        <h3>React Frontend + Python API</h3>
        <p>Frontend sends HTTP requests to FastAPI endpoints. Python hosts the analytics engine and returns JSON. React renders the response into a modern UI.</p>
      </article>
      <article className="card">
        <h3>Current Flow</h3>
        <p>React Frontend → FastAPI → CricketAnalyticsEngine → JSON Response → React UI</p>
      </article>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat-box">
      <span>{label}</span>
      <strong>{value ?? "--"}</strong>
    </div>
  );
}

function ListTable({ rows, columns }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column.replaceAll("_", " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((row, index) => (
              <tr key={index}>
                {columns.map((column) => (
                  <td key={column}>{formatValue(row[column])}</td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length}>No data available.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function JsonPreview({ data }) {
  if (!data) {
    return <div className="json-preview empty">No query result yet.</div>;
  }
  return <pre className="json-preview">{JSON.stringify(data, null, 2)}</pre>;
}

function emptyBatter() {
  return { runs: 0, balls: 0, fours: 0, sixes: 0, out: false, dismissal: "" };
}

function emptyBowler() {
  return { balls: 0, runs: 0, wickets: 0, maidens: 0 };
}

function defaultOversForFormat(format) {
  if (format === "T20I") return 20;
  if (format === "ODI") return 50;
  return "";
}

function maxOversPerBowler(state) {
  if (!isLimitedOvers(state.format)) return null;
  const overs = Number(state.maxOvers || defaultOversForFormat(state.format));
  if (!overs) return null;
  return Math.ceil(overs / 5);
}

function getBowlerQuotaError(bowlerName, state) {
  const limitOvers = maxOversPerBowler(state);
  if (!limitOvers || !bowlerName) return "";
  const balls = state.bowlers?.[bowlerName]?.balls || 0;
  if (balls >= limitOvers * 6) {
    return `${bowlerName} has already bowled the maximum ${limitOvers} overs for this ${state.format} innings.`;
  }
  return "";
}

function isLimitedOvers(format) {
  return format === "ODI" || format === "T20I";
}

function dismissalNeedsFielder(dismissal) {
  return ["caught", "run out", "stumped"].includes(dismissal);
}

function formatDismissal({ dismissal, fielder, bowler }) {
  if (dismissal === "caught") return `c ${fielder} b ${bowler}`;
  if (dismissal === "stumped") return `st ${fielder} b ${bowler}`;
  if (dismissal === "run out") return fielder ? `run out (${fielder})` : "run out";
  return dismissal;
}

function getMatchResult(state) {
  const innings = state.matchComplete ? state.innings || [] : [...(state.innings || []), inningsSnapshot(state)];
  const scores = Object.fromEntries(innings.map((inning) => [inning.battingTeam, Number(inning.totalRuns || 0)]));
  if (scores[state.teamA] === undefined || scores[state.teamB] === undefined) return "Match complete";
  if (scores[state.teamA] === scores[state.teamB]) return "Match tied";
  const winner = scores[state.teamA] > scores[state.teamB] ? state.teamA : state.teamB;
  return `${winner} won by ${Math.abs(scores[state.teamA] - scores[state.teamB])} runs`;
}

function isDismissalAllowed({ dismissal, extraType, freeHitActive }) {
  if (!dismissal) return true;
  if (freeHitActive) return FREE_HIT_DISMISSALS.has(dismissal);
  if (extraType === "no ball") return NO_BALL_DISMISSALS.has(dismissal);
  if (extraType === "wide") return dismissal === "run out" || dismissal === "stumped" || dismissal === "obstructing the field";
  return true;
}

function countsForBowler(dismissal) {
  return BOWLER_WICKET_TYPES.has(dismissal);
}

function inningsSnapshot(state) {
  return {
    battingTeam: state.battingTeam,
    bowlingTeam: state.bowlingTeam,
    inningsNumber: state.inningsNumber || 1,
    totalRuns: state.totalRuns,
    wickets: state.wickets,
    legalBalls: state.legalBalls,
    batters: state.batters,
    bowlers: state.bowlers,
    events: state.events || []
  };
}

function getPendingNameError(name, pending, state) {
  const cleanName = name.trim();
  if (!pending || !cleanName) return "";
  if (pending.type === "bowler" && cleanName === state.bowler) {
    return "A bowler cannot bowl two consecutive overs. Choose a different bowler.";
  }
  if (pending.type === "bowler") {
    const quotaError = getBowlerQuotaError(cleanName, state);
    if (quotaError) return quotaError;
  }
  if (pending.type === "batter") {
    if (cleanName === state.nonStriker) {
      return "The new batter cannot be the current non-striker.";
    }
    if (state.batters[cleanName]?.out) {
      return "This batter is already out. Enter another batter.";
    }
  }
  return "";
}

function snapshotScorerState(state) {
  return {
    ...state,
    batters: { ...state.batters },
    bowlers: { ...state.bowlers },
    pendingChanges: [...(state.pendingChanges || [])],
    innings: [...(state.innings || [])],
    events: (state.events || []).map(({ prevState, ...event }) => event),
    history: []
  };
}

function normalizeScorerState(state) {
  return {
    ...state,
    format: state.format || "ODI",
    maxOvers: state.maxOvers ?? defaultOversForFormat(state.format || "ODI"),
    ground: state.ground || "Local Ground",
    matchDate: state.matchDate || new Date().toISOString().slice(0, 10),
    inningsNumber: state.inningsNumber || 1,
    freeHitNext: Boolean(state.freeHitNext),
    matchComplete: Boolean(state.matchComplete),
    innings: state.innings || [],
    pendingChanges: state.pendingChanges || [],
    events: (state.events || []).map(({ prevState, ...event }) => event),
    history: (state.history || []).map((item) => snapshotScorerState(item))
  };
}

function formatOvers(balls = 0) {
  return `${Math.floor(balls / 6)}.${balls % 6}`;
}

function scorecardRows(state) {
  const activeOrder = [state.striker, state.nonStriker].filter(Boolean);
  return Object.entries(state.batters)
    .map(([player, stats]) => ({
      player,
      runs: stats.runs,
      balls: stats.balls,
      fours: stats.fours,
      sixes: stats.sixes,
      strike_rate: stats.balls ? (stats.runs * 100) / stats.balls : 0,
      status: stats.out ? (stats.dismissal || "out") : activeOrder.includes(player) ? "batting" : "not out"
    }))
    .sort((a, b) => {
      const activeA = activeOrder.indexOf(a.player);
      const activeB = activeOrder.indexOf(b.player);
      if (activeA !== -1 || activeB !== -1) {
        return (activeA === -1 ? 99 : activeA) - (activeB === -1 ? 99 : activeB);
      }
      if (a.status !== b.status) return a.status === "out" ? 1 : -1;
      return b.balls - a.balls || b.runs - a.runs;
    });
}

function bowlingRows(bowlers) {
  return Object.entries(bowlers).map(([bowler, stats]) => ({
    bowler,
    overs: formatOvers(stats.balls),
    runs: stats.runs,
    wickets: stats.wickets,
    economy: stats.balls ? (stats.runs * 6) / stats.balls : 0
  }));
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "--";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? value : value.toFixed(2);
  }
  return value;
}

export default App;
