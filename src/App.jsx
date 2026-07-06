import { useState, useRef, useEffect } from "react";
import { supabase } from "./lib/supabase";
import {
  validateStartTeam,
  validateChainLink,
  getStats,
  getRarityScore,
  getSuggestionOptions,
  getTeamSuggestionsForQuery,
  getTeamLeague,
  findAnyItem,
  getRandomChallenge,
  goalReached,
  getSetupSuggestions,
} from "./data/lookup.js";
import { loadPlayerUsage, recordPlayerUse } from "./data/playerUsage.js";
import { getDailyLinkChallenge } from "./data/pathSolver.js";

const TYPE_LABELS = { team: "TEAM", player: "PLAYER", college: "COLLEGE", number: "NUMBER" };
const TYPE_COLORS = { team: "#dd2222", player: "#1177dd", college: "#bb7700", number: "#1a9944" };
const TYPE_BG = {
  team: "rgba(221,34,34,0.05)",
  player: "rgba(17,119,221,0.05)",
  college: "rgba(187,119,0,0.05)",
  number: "rgba(26,153,68,0.05)",
};
const getHint = (type, item) => {
  if (type === "team") return `Enter a player who played for the ${item}`;
  if (type === "player") return `Enter ${item}'s team, college, or jersey number`;
  if (type === "college") return `Enter a player who went to ${item}`;
  if (type === "number") return `Enter a player who wore #${item}`;
  return "";
};
const TYPE_EMOJI = { player: "🏃‍♂️", number: "#️⃣", college: "🎓" };
const TEAM_LEAGUE_EMOJI = { MLB: "⚾️", NFL: "🏈", NBA: "🏀" };
function getItemEmoji(item) {
  if (item.type === "team") return TEAM_LEAGUE_EMOJI[getTeamLeague(item.name)] || "🏅";
  return TYPE_EMOJI[item.type] || "❓";
}

function History({ history, showPoints }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [history]);

  return (
    <div ref={ref} className="history-box">
      {history.map((item, i) => (
        <div key={i} className="history-item">
          <div
            className="history-link"
            style={{ borderLeft: `3px solid ${TYPE_COLORS[item.type]}` }}
          >
            <span
              className="history-badge"
              style={{ background: TYPE_COLORS[item.type] }}
            >
              {TYPE_LABELS[item.type]}
            </span>

            <span
              className="history-name"
              style={{ color: TYPE_COLORS[item.type] }}
            >
              {item.name}
            </span>

            {showPoints && item.points > 0 && (
              <span className="history-pts">{item.points}</span>
            )}
          </div>

          {i < history.length - 1 && (
            <div className="chain-connector">
              <div className="chain-dot" />
              <div className="chain-line" />
              <div className="chain-dot" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function Landing({ onFreePlay, onDaily, onRarity, onChallenge, onRules, onPrivacy, onReport }) {
  const stats = getStats();
  const today = new Date().toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const daily = getDailyLinkChallenge();

  return (
    <div className="landing">
      <div className="logo-area">
        <h1 className="title">SPORTS LINK</h1>
        <p className="tagline">Connect teams, players, colleges &amp; numbers.</p>
      </div>

      {/* Hero: Daily Challenge */}
      <div className="daily-hero">
        <div className="daily-hero-header">
          <div className="daily-dot" />
          <span className="daily-kicker-label">DAILY LINK</span>
          <span className="daily-hero-date">{today}</span>
        </div>

        <div className="daily-hero-route">
          <div className="daily-hero-node">
            <div className="daily-card-label">START</div>
            <div className="daily-hero-name">{daily.startName}</div>
          </div>
          <div className="daily-hero-arrow">→</div>
          <div className="daily-hero-node">
            <div className="daily-card-label">GOAL</div>
            <div className="daily-hero-name">{daily.goalName}</div>
          </div>
        </div>

        <div className="daily-hero-par">
          Par: {daily.par} Links
        </div>

        <button className="play-today-btn" onClick={onDaily}>
          PLAY TODAY
        </button>
      </div>

      {/* Secondary modes */}
      <div className="secondary-modes">
        <button className="mode-btn free-btn" onClick={onFreePlay}>
          <div className="mode-btn-title">FREE PLAY</div>
          <div className="mode-btn-desc">Pick any team. No limits.</div>
        </button>

        <button className="mode-btn challenge-friend-btn" onClick={onChallenge}>
          <div className="mode-btn-top">
            <span className="mode-btn-icon">🔗</span>
            <span className="mode-btn-title">CHALLENGE A FRIEND</span>
          </div>
          <div className="mode-btn-desc">Set a chain, share the link.</div>
        </button>
      </div>

      <div className="how-it-works">
        <div className="how-label">EXAMPLE CHAIN</div>
        <div className="how-chain">
          <span className="how-pill how-team">Pirates</span>
          <span className="how-arr">→</span>
          <span className="how-pill how-player">Paul Skenes</span>
          <span className="how-arr">→</span>
          <span className="how-pill how-college">LSU</span>
          <span className="how-arr">→</span>
          <span className="how-pill how-player">Ja'Marr Chase</span>
          <span className="how-arr">→</span>
          <span className="how-pill how-number">1</span>
          <span className="how-arr">→</span>
          <span className="how-pill how-player">Victor Wembanyama</span>
          <span className="how-arr">→</span>
          <span className="how-pill how-team">Spurs</span>
        </div>
      </div>

      <div className="stats-bar">
        <div className="stat">
          <span className="stat-num">{stats.players}</span>
          <span className="stat-label">PLAYERS</span>
        </div>
        <div className="stat-divider" />
        <div className="stat">
          <span className="stat-num">{stats.teams}</span>
          <span className="stat-label">TEAMS</span>
        </div>
        <div className="stat-divider" />
        <div className="stat">
          <span className="stat-num">{stats.colleges}</span>
          <span className="stat-label">COLLEGES</span>
        </div>
      </div>

      <p className="league-tags">
        <span className="league-tag">NFL</span>
        <span className="league-tag">NBA</span>
        <span className="league-tag">MLB</span>
      </p>

      <div className="landing-footer-links">
        <button className="rules-page-link" onClick={onRules}>How to Play</button>
        <span className="landing-footer-sep">·</span>
        <button className="rules-page-link" onClick={onPrivacy}>Privacy Policy</button>
        <span className="landing-footer-sep">·</span>
        <button className="rules-page-link" onClick={onReport}>Report Error</button>
      </div>
    </div>
  );
}

function ChallengeSetup({ onBack, onPlay }) {
  const [tab, setTab] = useState("random");
  const [random, setRandom] = useState(() => getRandomChallenge());
  const [startInput, setStartInput] = useState("");
  const [goalInput, setGoalInput] = useState("");
  const [startItem, setStartItem] = useState(null);
  const [goalItem, setGoalItem] = useState(null);
  const [startErr, setStartErr] = useState("");
  const [goalErr, setGoalErr] = useState("");
  const [startSugs, setStartSugs] = useState([]);
  const [goalSugs, setGoalSugs] = useState([]);
  const [copiedLink, setCopiedLink] = useState(false);
  const pickedRef = useRef(false);

  const resolveField = (value, setItem, setErr) => {
    if (!value.trim()) return;
    const result = findAnyItem(value);
    if (result) { setItem(result); setErr(""); }
    else { setItem(null); setErr("Not recognized. Try a team, player, college, or jersey number."); }
  };

  const pickSuggestion = (sug, setInput, setItem, setErr, setSugs) => {
    pickedRef.current = true;
    setInput(sug.name);
    setItem(sug);
    setErr("");
    setSugs([]);
  };

  const handleBlur = (value, setItem, setErr, setSugs) => {
    setTimeout(() => {
      if (!pickedRef.current) resolveField(value, setItem, setErr);
      pickedRef.current = false;
      setSugs([]);
    }, 150);
  };

  const activeChallenge = tab === "random"
    ? random
    : (startItem && goalItem ? { startName: startItem.name, startType: startItem.type, goalName: goalItem.name, goalType: goalItem.type } : null);

  const copyLink = async () => {
    if (!activeChallenge) return;
    const params = new URLSearchParams({
      start: activeChallenge.startName,
      startType: activeChallenge.startType,
      goal: activeChallenge.goalName,
      goalType: activeChallenge.goalType,
    });
    const url = `https://sportslinkgame.com?${params}`;
    try { await navigator.clipboard.writeText(url); }
    catch {
      const ta = document.createElement("textarea");
      ta.value = url; document.body.appendChild(ta); ta.select();
      document.execCommand("copy"); document.body.removeChild(ta);
    }
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2500);
  };

  return (
    <div className="container">
      <div className="challenge-setup">
        <button className="back-btn" onClick={onBack}>← MENU</button>

        <div className="challenge-setup-header">
          <div className="rules-kicker">SPORTS LINK</div>
          <h1 className="challenge-setup-title">Challenge</h1>
          <p className="challenge-setup-desc">Set a chain. Share the link. See who can solve it in fewer links.</p>
        </div>

        <div className="challenge-tabs">
          <button className={`challenge-tab-btn${tab === "random" ? " active" : ""}`} onClick={() => setTab("random")}>Random</button>
          <button className={`challenge-tab-btn${tab === "custom" ? " active" : ""}`} onClick={() => setTab("custom")}>Custom</button>
        </div>

        {tab === "random" && (
          <div className="challenge-card">
            <div className="challenge-route">
              <div className="challenge-node">
                <div className="challenge-node-label">{TYPE_LABELS[random.startType]}</div>
                <div className="challenge-node-name">{random.startName}</div>
              </div>
              <div className="challenge-arrow">→</div>
              <div className="challenge-node">
                <div className="challenge-node-label">{TYPE_LABELS[random.goalType]}</div>
                <div className="challenge-node-name">{random.goalName}</div>
              </div>
            </div>
            <button className="challenge-refresh-btn" onClick={() => setRandom(getRandomChallenge())}>🔀 New Random</button>
          </div>
        )}

        {tab === "custom" && (
          <div className="challenge-custom">
            <div className="challenge-custom-field">
              <label className="report-label">Start</label>
              <div className="challenge-input-wrap">
                <input
                  className="report-input"
                  placeholder="Team, player, college, or number"
                  value={startInput}
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck="false"
                  inputMode="text"
                  onChange={(e) => {
                    const v = e.target.value;
                    setStartInput(v); setStartItem(null); setStartErr("");
                    setStartSugs(getSetupSuggestions(v));
                  }}
                  onBlur={() => handleBlur(startInput, setStartItem, setStartErr, setStartSugs)}
                />
                {startSugs.length > 0 && (
                  <div className="suggestions-box">
                    {startSugs.map((s) => (
                      <button key={s.name} className="suggestion-item" onMouseDown={() => pickSuggestion(s, setStartInput, setStartItem, setStartErr, setStartSugs)}>
                        <span className={`sug-type-badge sug-${s.type}`}>{TYPE_LABELS[s.type]}</span>
                        {s.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {startErr && <p className="report-error">{startErr}</p>}
              {startItem && (
                <div className="challenge-resolved">
                  <span className={`how-pill how-${startItem.type}`}>{TYPE_LABELS[startItem.type]}</span>
                  <span className="challenge-resolved-name">{startItem.name}</span>
                </div>
              )}
            </div>
            <div className="challenge-custom-field">
              <label className="report-label">Goal</label>
              <div className="challenge-input-wrap">
                <input
                  className="report-input"
                  placeholder="Team, player, college, or number"
                  value={goalInput}
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck="false"
                  inputMode="text"
                  onChange={(e) => {
                    const v = e.target.value;
                    setGoalInput(v); setGoalItem(null); setGoalErr("");
                    setGoalSugs(getSetupSuggestions(v));
                  }}
                  onBlur={() => handleBlur(goalInput, setGoalItem, setGoalErr, setGoalSugs)}
                />
                {goalSugs.length > 0 && (
                  <div className="suggestions-box">
                    {goalSugs.map((s) => (
                      <button key={s.name} className="suggestion-item" onMouseDown={() => pickSuggestion(s, setGoalInput, setGoalItem, setGoalErr, setGoalSugs)}>
                        <span className={`sug-type-badge sug-${s.type}`}>{TYPE_LABELS[s.type]}</span>
                        {s.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {goalErr && <p className="report-error">{goalErr}</p>}
              {goalItem && (
                <div className="challenge-resolved">
                  <span className={`how-pill how-${goalItem.type}`}>{TYPE_LABELS[goalItem.type]}</span>
                  <span className="challenge-resolved-name">{goalItem.name}</span>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="btn-row" style={{ marginTop: 20 }}>
          <button className="btn-primary" disabled={!activeChallenge} onClick={() => activeChallenge && onPlay(activeChallenge)}>
            Play
          </button>
          <button className="btn-share" disabled={!activeChallenge} onClick={copyLink}>
            {copiedLink ? "✓ COPIED!" : "🔗 Share Link"}
          </button>
        </div>
      </div>
    </div>
  );
}

function PrivacyPage({ onBack }) {
  return (
    <div className="container">
      <div className="rules-page">
        <button className="back-btn" onClick={onBack}>← MENU</button>

        <div className="rules-page-header">
          <div className="rules-kicker">SPORTS LINK</div>
          <h1 className="rules-page-title">Privacy Policy</h1>
          <p className="rules-page-p" style={{ marginTop: 8, textAlign: "center" }}>Last updated: June 4, 2026</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Overview</h2>
          <p className="rules-page-p">Sports Link is a free, browser-based game. We are committed to keeping your experience simple and your data minimal. We do not sell, share, or monetize any information about our users.</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Data We Collect</h2>
          <p className="rules-page-p">We collect limited, anonymous usage data to improve the game. Specifically, we track which players are used in chains in aggregate — no personal information is attached to this data. We also store any error reports you voluntarily submit through the "Report Error" form, which includes only what you type into that form.</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Local Storage</h2>
          <p className="rules-page-p">We use your browser's local storage solely to remember whether you have seen the tutorial. This data never leaves your device and is not transmitted to any server.</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Third-Party Services</h2>
          <p className="rules-page-p">Sports Link uses Supabase to store aggregate player usage data and error report submissions. Supabase's own privacy policy governs how they handle that data. We do not use advertising networks, tracking pixels, or any other third-party analytics beyond what is inherent to our hosting provider (Vercel).</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Cookies</h2>
          <p className="rules-page-p">We do not use cookies.</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Children's Privacy</h2>
          <p className="rules-page-p">Sports Link does not knowingly collect any information from children under the age of 13. The game is intended for general audiences and requires no account or personal information to play.</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Changes to This Policy</h2>
          <p className="rules-page-p">We may update this policy from time to time. Any changes will be reflected on this page with an updated date.</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Contact</h2>
          <p className="rules-page-p">If you have any questions about this privacy policy, you can reach us through the "Report Error" form in the app.</p>
        </div>
      </div>
    </div>
  );
}

function RulesPage({ onBack, onReport }) {
  return (
    <div className="container">
      <div className="rules-page">
        <button className="back-btn" onClick={onBack}>← MENU</button>

        <div className="rules-page-header">
          <div className="rules-kicker">SPORTS LINK</div>
          <h1 className="rules-page-title">How to Play</h1>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Building a Chain</h2>
          <p className="rules-page-p">Connect teams, players, colleges, and jersey numbers in a continuous chain. Each link must be valid — a real connection in the data.</p>
          <div className="rules-page-rows">
            <div className="rules-page-row">
              <span className="how-pill how-team">TEAM</span>
              <span className="rules-page-arrow">→</span>
              <span className="rules-page-text">Name a player who played for that team</span>
            </div>
            <div className="rules-page-row">
              <span className="how-pill how-player">PLAYER</span>
              <span className="rules-page-arrow">→</span>
              <span className="rules-page-text">Name one of their teams, their college, or a jersey number they wore</span>
            </div>
            <div className="rules-page-row">
              <span className="how-pill how-college">COLLEGE</span>
              <span className="rules-page-arrow">→</span>
              <span className="rules-page-text">Name a player who attended that school</span>
            </div>
            <div className="rules-page-row">
              <span className="how-pill how-number">NUMBER</span>
              <span className="rules-page-arrow">→</span>
              <span className="rules-page-text">Name a player who wore that jersey number</span>
            </div>
          </div>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Wrong Answers</h2>
          <p className="rules-page-p">A wrong answer ends the game immediately. The game checks that the connection actually exists in the database, so make sure the link is real before submitting.</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">No Backtracking</h2>
          <p className="rules-page-p">You cannot go straight back to the item you just came from. For example, if your chain is <strong>Eagles → Jalen Hurts</strong>, you cannot immediately say <strong>Eagles</strong> again. You can revisit a team or player later through a different path.</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Daily Challenge</h2>
          <p className="rules-page-p">Each day a new challenge is posted with a fixed start team and a goal team. Your goal is to build a chain from start to goal in as few links as possible. The par score is shown on the menu — try to match or beat it.</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Free Play</h2>
          <p className="rules-page-p">Pick any NFL, NBA, or MLB team to start. Build the longest or rarest chain you can — there's no goal and no limit.</p>
        </div>

        <div className="rules-page-section">
          <h2 className="rules-page-h2">Data</h2>
          <p className="rules-page-p">The database covers NFL, NBA, and MLB players and is updated periodically. The most recent update was around <strong>May 23, 2026</strong>. Some data gaps may exist — if a valid connection isn't being accepted, use the <button className="rules-page-inline-btn" onClick={onReport}>Report Error</button> button to let us know and we'll get it fixed.</p>
        </div>
      </div>
    </div>
  );
}

function ReportOverlay({ onClose }) {
  const [searchedFor, setSearchedFor] = useState("");
  const [correctAnswer, setCorrectAnswer] = useState("");
  const [note, setNote] = useState("");
  const [status, setStatus] = useState(null); // "submitting" | "success" | "error"

  const submit = async (e) => {
    e.preventDefault();
    if (!searchedFor.trim() || !correctAnswer.trim()) return;
    setStatus("submitting");
    const { error } = await supabase.from("data_reports").insert({
      searched_for: searchedFor.trim(),
      correct_answer: correctAnswer.trim(),
      note: note.trim() || null,
    });
    setStatus(error ? "error" : "success");
  };

  return (
    <div className="rules-overlay" onClick={onClose}>
      <div className="rules-card report-card" onClick={(e) => e.stopPropagation()}>
        <button className="rules-close" onClick={onClose}>×</button>
        <div className="rules-kicker">HELP US IMPROVE</div>
        <h2 className="rules-title">Report Missing Data</h2>

        {status === "success" ? (
          <div className="report-success">
            <div className="report-success-icon">✓</div>
            <p>Thanks! We'll review your report.</p>
            <button className="btn-primary" onClick={onClose}>Close</button>
          </div>
        ) : (
          <form className="report-form" onSubmit={submit}>
            <div className="report-field">
              <label className="report-label">What did you search for?</label>
              <input
                className="report-input"
                type="text"
                placeholder="e.g. A.J. Brown, Notre Dame"
                value={searchedFor}
                onChange={(e) => setSearchedFor(e.target.value)}
                required
              />
            </div>
            <div className="report-field">
              <label className="report-label">What should the correct answer be?</label>
              <input
                className="report-input"
                type="text"
                placeholder="e.g. Player should link to Eagles"
                value={correctAnswer}
                onChange={(e) => setCorrectAnswer(e.target.value)}
                required
              />
            </div>
            <div className="report-field">
              <label className="report-label">Additional notes <span className="report-optional">(optional)</span></label>
              <textarea
                className="report-input report-textarea"
                placeholder="Any extra context..."
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={3}
              />
            </div>
            {status === "error" && (
              <p className="report-error">Something went wrong. Please try again.</p>
            )}
            <button
              className="btn-primary"
              type="submit"
              disabled={status === "submitting" || !searchedFor.trim() || !correctAnswer.trim()}
            >
              {status === "submitting" ? "Submitting..." : "Submit Report"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

function RulesOverlay({ onClose }) {
  return (
    <div className="rules-overlay" onClick={onClose}>
      <div className="rules-card" onClick={(e) => e.stopPropagation()}>
        <button className="rules-close" onClick={onClose}>×</button>
        <div className="rules-kicker">HOW TO PLAY</div>
        <h2 className="rules-title">The Rules</h2>
        <div className="rules-list">
          <div className="rules-item">
            <span className="rules-badge" style={{ background: TYPE_COLORS.team }}>TEAM</span>
            <span className="rules-text">Name a player who played for this team</span>
          </div>
          <div className="rules-item">
            <span className="rules-badge" style={{ background: TYPE_COLORS.player }}>PLAYER</span>
            <span className="rules-text">Name a team they played on, their college, or a jersey number they wore</span>
          </div>
          <div className="rules-item">
            <span className="rules-badge" style={{ background: TYPE_COLORS.college }}>COLLEGE</span>
            <span className="rules-text">Name a player who attended this school</span>
          </div>
          <div className="rules-item">
            <span className="rules-badge" style={{ background: TYPE_COLORS.number }}>NUMBER</span>
            <span className="rules-text">Name a player who wore this jersey number</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function Game({ onBack, modeType = "free", rarityLength = 10, challengeStart = null, challengeStartType = null, challengeGoal = null, challengeGoalType = null }) {
  const dailyChallenge = modeType === "daily" ? getDailyLinkChallenge() : null;

  const isDaily = modeType === "daily";
  const isRarity = modeType === "rarity";
  const isChallenge = modeType === "challenge";
  const hasGoal = isDaily || isChallenge;
  const showPoints = false;

  const startName = isDaily ? dailyChallenge.startName : isChallenge ? challengeStart : null;
  const startType = isDaily ? dailyChallenge.startType : isChallenge ? challengeStartType : null;
  const goalName = isDaily ? dailyChallenge.goalName : isChallenge ? challengeGoal : null;
  const goalType = isDaily ? dailyChallenge.goalType : isChallenge ? challengeGoalType : null;

  const maxLinks = isRarity ? rarityLength : Infinity;

  const [phase, setPhase] = useState(hasGoal ? "playing" : "start");
  const [history, setHistory] = useState(
    hasGoal ? [{ name: startName, type: startType, points: 0 }] : []
  );
  const [currentItem, setCurrentItem] = useState(hasGoal ? startName : null);
  const [currentType, setCurrentType] = useState(hasGoal ? startType : null);
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [gameOver, setGameOver] = useState(false);
  const [wrongAnswer, setWrongAnswer] = useState(null);
  const [flash, setFlash] = useState(false);
  const [totalScore, setTotalScore] = useState(0);
  const [shared, setShared] = useState(false);
  const [sharedLink, setSharedLink] = useState(false);
  const [suggestions, setSuggestions] = useState([]);

  const inputRef = useRef(null);

  useEffect(() => {
    if (inputRef.current) inputRef.current.focus();
  }, [phase, error, history]);

  const triggerFlash = () => {
    setFlash(true);
    setTimeout(() => setFlash(false), 400);
  };

  const linksUsed = history.length > 0 ? history.length - 1 : 0;
  const atLimit = isRarity && linksUsed >= maxLinks;

  const lastItem = history.length > 0 ? history[history.length - 1] : null;
  const reachedGoal = hasGoal && !!lastItem && goalReached(lastItem.name, lastItem.type, goalName, goalType);

  const updateSuggestions = (value) => {
    const query = value.trim().toLowerCase();

    if (!query || query.length < 2) {
      setSuggestions([]);
      return;
    }

    const fuzzyNorm = (s) => s.toLowerCase().replace(/[.\-']/g, "");
    const normQuery = fuzzyNorm(query);

    const filterOptions = (options) => {
      const sw = options.filter((o) => {
        const lo = o.toLowerCase();
        return lo.startsWith(query) || fuzzyNorm(o).startsWith(normQuery);
      });
      const inc = options.filter((o) => {
        if (sw.includes(o)) return false;
        const lo = o.toLowerCase();
        return lo.includes(query) || fuzzyNorm(o).includes(normQuery);
      });
      return [...sw, ...inc];
    };

    if (currentType === "player") {
      const teamMatches = getTeamSuggestionsForQuery(value.trim());
      const collegeMatches = filterOptions(getSuggestionOptions("college"));
      const seen = new Set(teamMatches);
      const colleges = collegeMatches.filter((c) => !seen.has(c));
      setSuggestions([...teamMatches, ...colleges].slice(0, 8));
      return;
    }

    let type = null;
    if (currentType === "team" || currentType === "college" || currentType === "number") {
      type = "player";
    }

    if (!type) {
      setSuggestions([]);
      return;
    }

    setSuggestions(filterOptions(getSuggestionOptions(type)).slice(0, 8));
  };

  const startGame = () => {
    if (!input.trim()) return;

    setError("");

    const result = validateStartTeam(input.trim());

    if (result.valid) {
      const name = result.corrected_name;

      setCurrentItem(name);
      setCurrentType("team");
      setHistory([{ name, type: "team", points: 0 }]);
      setPhase("playing");
      setInput("");
      setSuggestions([]);
      triggerFlash();
    } else {
      setError(result.explanation);
    }
  };

  const submitAnswerValue = (rawValue) => {
    const answerValue = String(rawValue || "").trim();

    if (!answerValue || atLimit) return;

    setError("");

    const result = validateChainLink(currentItem, currentType, answerValue);

    if (result.valid) {
      const name = result.corrected_name;
      const type = result.type;

      const prevItem = history.length >= 2 ? history[history.length - 2] : null;
      if (prevItem && prevItem.name === name) {
        setError(`You just came from ${name} — you can't go straight back.`);
        return;
      }

      if (type === "player") {
        recordPlayerUse(name);
      }

      const points = showPoints
        ? getRarityScore(currentItem, currentType, name, type)
        : 0;

      const newHistory = [...history, { name, type, points }];

      setHistory(newHistory);
      setCurrentItem(name);
      setCurrentType(type);
      setInput("");
      setSuggestions([]);
      setTotalScore((s) => s + points);
      triggerFlash();

      if (hasGoal && goalReached(name, type, goalName, goalType)) {
        setTimeout(() => setGameOver(true), 600);
      }

      if (isRarity && newHistory.length - 1 >= maxLinks) {
        setTimeout(() => setGameOver(true), 600);
      }
    } else {
      setSuggestions([]);
      setWrongAnswer({
        answer: answerValue,
        explanation: result.explanation,
      });
      setGameOver(true);
    }
  };

  const submitAnswer = () => {
    submitAnswerValue(input);
  };

  const giveUp = () => {
    setGameOver(true);
  };

  const reset = () => {
    if (hasGoal) {
      setHistory([{ name: startName, type: startType, points: 0 }]);
      setCurrentItem(startName);
      setCurrentType(startType);
      setPhase("playing");
    } else {
      setHistory([]);
      setCurrentItem(null);
      setCurrentType(null);
      setPhase("start");
    }

    setInput("");
    setError("");
    setGameOver(false);
    setWrongAnswer(null);
    setTotalScore(0);
    setShared(false);
    setSuggestions([]);
  };

  const shareResult = async () => {
    const today = new Date().toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });

    const chain = history.map((h) => getItemEmoji(h)).join("");

    let modeLabel = "Free Play";
    if (isDaily) modeLabel = "Daily Link";
    if (isRarity) modeLabel = `Rarity Run ${rarityLength}`;
    if (isChallenge) modeLabel = "Challenge";

    let text = `🔗 Sports Link ${modeLabel} — ${today}\n\n`;

    if (hasGoal) {
      text += `${startName} → ${goalName}\n`;
    }

    text += `${chain}\n\n`;
    text += `${linksUsed} link${linksUsed !== 1 ? "s" : ""}`;

    if (showPoints) {
      text += ` · ${totalScore} pts`;
    }

    text += wrongAnswer ? " ❌" : " ✅";
    text += "\n\nsportslinkgame.com";

    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }

    setShared(true);
    setTimeout(() => setShared(false), 2500);
  };

  const shareChallengeResult = async () => {
    const today = new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" });
    const chain = history.map((h) => getItemEmoji(h)).join("");
    const params = new URLSearchParams({ start: startName, startType, goal: goalName, goalType });
    const url = `sportslinkgame.com?${params}`;

    let text = `🔗 Sports Link Challenge — ${today}\n\n`;
    text += `${startName} → ${goalName}\n`;
    text += `${chain}\n\n`;
    text += `${linksUsed} link${linksUsed !== 1 ? "s" : ""}`;
    text += wrongAnswer ? " ❌" : " ✅";
    text += `\n\nCan you beat me? \nhttps://${url}`;

    try { await navigator.clipboard.writeText(text); }
    catch {
      const ta = document.createElement("textarea");
      ta.value = text; document.body.appendChild(ta); ta.select();
      document.execCommand("copy"); document.body.removeChild(ta);
    }
    setSharedLink(true);
    setTimeout(() => setSharedLink(false), 2500);
  };

  const activeColor = currentType ? TYPE_COLORS[currentType] : "#ff4444";
  const activeBg = currentType ? TYPE_BG[currentType] : "transparent";

  if (gameOver) {
    const completed = !wrongAnswer && (reachedGoal || atLimit || modeType === "free" || isChallenge);

    return (
      <div className="container">
        <div className="game-over-box">
          <div className="game-over-icon">
            {wrongAnswer ? "❌" : completed ? "🏆" : "🏁"}
          </div>

          <div className="game-over-title">
            {wrongAnswer ? "GAME OVER" : "COMPLETE!"}
          </div>

          {hasGoal && (
            <div className="daily-challenge-box">
              <div className="daily-challenge-label">{isChallenge ? "CHALLENGE" : "DAILY LINK"}</div>
              <div className="daily-challenge-route">
                <span className="daily-node start">{startName}</span>
                <span className="daily-arrow">→</span>
                <span className="daily-node goal">{goalName}</span>
              </div>
              {isDaily && <div className="daily-par">Par: {dailyChallenge.par}</div>}
            </div>
          )}

          {wrongAnswer && (
            <div className="wrong-answer-box">
              <div className="wrong-answer-text">"{wrongAnswer.answer}"</div>
              <div className="wrong-answer-reason">{wrongAnswer.explanation}</div>
            </div>
          )}

          <div className="final-score-row">
            <span className="final-score">{linksUsed}</span>
            <span className="final-score-label">
              LINK{linksUsed !== 1 ? "S" : ""}
            </span>

            {showPoints && (
              <>
                <span className="score-divider">·</span>
                <span className="final-score">{totalScore}</span>
                <span className="final-score-label">PTS</span>
              </>
            )}
          </div>

          <History history={history} showPoints={showPoints} />

          <div className="btn-row">
            {isChallenge ? (
              <button className="btn-share" onClick={shareChallengeResult}>
                {sharedLink ? "✓ COPIED!" : "🔗 SHARE CHALLENGE"}
              </button>
            ) : (
              <button className="btn-share" onClick={shareResult}>
                {shared ? "✓ COPIED!" : "📋 SHARE RESULT"}
              </button>
            )}
          </div>

          <div className="btn-row">
            <button className="btn-primary" onClick={reset}>
              PLAY AGAIN
            </button>

            <button className="btn-secondary" onClick={onBack}>
              MENU
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="header">
        <button className="back-btn" onClick={onBack}>
          ← MENU
        </button>

        <div className="score-area">
          {(isDaily || isRarity || isChallenge) && (
            <div className="score-pill links-pill">
              <span className="score-pill-label">LINKS</span>
              <span className="score-pill-num">
                {isRarity ? `${linksUsed}/${maxLinks}` : linksUsed}
              </span>
            </div>
          )}

          <div className="score-pill">
            <span className="score-pill-label">
              {showPoints ? "SCORE" : "CHAIN"}
            </span>

            <span className="score-pill-num">
              {showPoints ? totalScore : history.length}
            </span>
          </div>
        </div>
      </div>

      {hasGoal && (
        <div className="daily-challenge-box">
          <div className="daily-challenge-label">{isChallenge ? "CHALLENGE" : "DAILY LINK"}</div>
          <div className="daily-challenge-route">
            <span className="daily-node start">{startName}</span>
            <span className="daily-arrow">→</span>
            <span className="daily-node goal">{goalName}</span>
          </div>
          {isDaily && <div className="daily-par">Par: {dailyChallenge.par}</div>}
        </div>
      )}

      {isRarity && (
        <div className="daily-challenge-box">
          <div className="daily-challenge-label">RARITY RUN</div>
          <div className="daily-challenge-route">
            <span className="daily-node goal">{rarityLength} Links</span>
          </div>
          <div className="daily-par">
            Higher score = rarer chain. Starting team is free.
          </div>
        </div>
      )}

      {phase === "start" && (
        <div className="start-box">
          <div className="mode-title">START YOUR CHAIN</div>
          <p className="mode-desc">Pick any NFL, NBA, or MLB team to begin.</p>

          <div className="input-row">
            <input
              ref={inputRef}
              type="search"
              className="game-input"
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
              spellCheck="false"
              inputMode="text"
              style={{ borderColor: "#ff4444", color: "#ff4444" }}
              placeholder="Enter a team..."
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                setError("");
              }}
              onKeyDown={(e) => e.key === "Enter" && startGame()}
            />

            <button
              className="btn-submit"
              style={{ background: "#ff4444" }}
              onClick={startGame}
            >
              GO
            </button>
          </div>

          {error && <div className="error">{error}</div>}
        </div>
      )}

      {phase === "playing" && (
        <div className="play-box">
          <div
            className={`current-section ${flash ? "flash" : ""}`}
            style={{ borderColor: activeColor, background: activeBg }}
          >
            <div className="current-top-row">
              <span
                className="type-badge"
                style={{ background: activeColor }}
              >
                {TYPE_LABELS[currentType]}
              </span>

              <span className="current-label">CURRENT</span>
            </div>

            <div className="current-value" style={{ color: activeColor }}>
              {currentItem}
            </div>

            <div className="hint">{getHint(currentType, currentItem)}</div>
          </div>

          {history.length > 0 && (
            <History history={history} showPoints={showPoints} />
          )}

          {!atLimit && (
            <>
              <div className="input-row">
                <input
                  ref={inputRef}
                  type="search"
                  className="game-input"
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck="false"
                  inputMode="text"
                  style={{
                    borderColor: activeColor,
                    color: activeColor,
                    background: activeBg,
                  }}
                  placeholder="Your answer..."
                  value={input}
                  onChange={(e) => {
                    setInput(e.target.value);
                    setError("");
                    updateSuggestions(e.target.value);
                  }}
                  onKeyDown={(e) => e.key === "Enter" && submitAnswer()}
                />

                <button
                  className="btn-submit"
                  style={{ background: activeColor }}
                  onClick={submitAnswer}
                >
                  →
                </button>
              </div>

              {suggestions.length > 0 && (
                <div className="suggestions-box">
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      className="suggestion-item"
                      onClick={() => submitAnswerValue(s)}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}

              {error && <div className="error">{error}</div>}

              {!isDaily && (
                <button className="give-up-btn" onClick={giveUp}>
                  I'M STUCK — END GAME
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}


export default function App() {
  const [challengeData, setChallengeData] = useState(() => {
    const p = new URLSearchParams(window.location.search);
    const start = p.get("start"), startType = p.get("startType");
    const goal = p.get("goal"), goalType = p.get("goalType");
    if (start && startType && goal && goalType) {
      return { startName: decodeURIComponent(start), startType, goalName: decodeURIComponent(goal), goalType };
    }
    return null;
  });
  const [mode, setMode] = useState(() => {
    const p = new URLSearchParams(window.location.search);
    return (p.get("start") && p.get("goal")) ? "challenge" : null;
  });
  const [rarityLength, setRarityLength] = useState(10);
  const [showTutorial, setShowTutorial] = useState(() => {
    return localStorage.getItem("sportsLinkTutorialSeen") !== "true";
  });
  const [showRules, setShowRules] = useState(false);
  const [showReport, setShowReport] = useState(false);

  function closeTutorial() {
    localStorage.setItem("sportsLinkTutorialSeen", "true");
    setShowTutorial(false);
  }

  useEffect(() => {
    loadPlayerUsage();
  }, []);

  let screen;

  if (mode === "free") {
    screen = <Game onBack={() => setMode(null)} modeType="free" />;
  } else if (mode === "daily") {
    screen = <Game onBack={() => setMode(null)} modeType="daily" />;
  } else if (mode === "rarity") {
    screen = (
      <Game
        onBack={() => setMode(null)}
        modeType="rarity"
        rarityLength={rarityLength}
      />
    );
  } else if (mode === "challenge-setup") {
    screen = (
      <ChallengeSetup
        onBack={() => setMode(null)}
        onPlay={(c) => { setChallengeData(c); setMode("challenge"); }}
      />
    );
  } else if (mode === "challenge") {
    screen = (
      <Game
        onBack={() => setMode(null)}
        modeType="challenge"
        challengeStart={challengeData?.startName}
        challengeStartType={challengeData?.startType}
        challengeGoal={challengeData?.goalName}
        challengeGoalType={challengeData?.goalType}
      />
    );
  } else if (mode === "rules") {
    screen = <RulesPage onBack={() => setMode(null)} onReport={() => { setMode(null); setShowReport(true); }} />;
  } else if (mode === "privacy") {
    screen = <PrivacyPage onBack={() => setMode(null)} />;
  } else {
    screen = (
      <div className="container">
        {showTutorial && (
          <div className="tutorial-overlay">
            <div className="tutorial-card">
              <button className="tutorial-close" onClick={closeTutorial}>
                ×
              </button>

              <div className="tutorial-kicker">HOW TO PLAY</div>
              <h2>Build A Sports Chain</h2>

              <p>Connect teams, players, colleges, and jersey numbers.</p>

              <div className="tutorial-example">
                <span>Pirates</span>
                <span>→</span>
                <span>Paul Skenes</span>
                <span>→</span>
                <span>LSU</span>
                <span>→</span>
                <span>Ja'Marr Chase</span>
                <span>→</span>
                <span>1</span>
                <span>→</span>
                <span>Victor Wembanyama</span>
                <span>→</span>
                <span>Spurs</span>
              </div>

              <div className="tutorial-rules">
                <p><strong>Teams</strong> connect to players who played for them.</p>
                <p><strong>Players</strong> connect to their teams, colleges, or numbers.</p>
                <p><strong>Colleges and numbers</strong> connect back to players.</p>
              </div>

              <button className="tutorial-btn" onClick={closeTutorial}>
                Start Playing
              </button>
            </div>
          </div>
        )}

        <Landing
          onFreePlay={() => setMode("free")}
          onDaily={() => setMode("daily")}
          onRarity={(len) => {
            setRarityLength(len);
            setMode("rarity");
          }}
          onChallenge={() => setMode("challenge-setup")}
          onRules={() => setMode("rules")}
          onPrivacy={() => setMode("privacy")}
          onReport={() => setShowReport(true)}
        />
      </div>
    );
  }

  return (
    <>
      {screen}
      <button
        className="rules-fab"
        onClick={() => setShowRules(true)}
        aria-label="Rules"
      >
        ?
      </button>
      {showRules && <RulesOverlay onClose={() => setShowRules(false)} />}
      {showReport && <ReportOverlay onClose={() => setShowReport(false)} />}
    </>
  );
}
