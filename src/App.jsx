import { useState, useRef, useEffect } from "react";
import { supabase } from "./lib/supabase";
import {
  validateStartTeam,
  validateChainLink,
  getStats,
  getRarityScore,
  getSuggestionOptions,
} from "./data/lookup.js";
import { getDailyLinkChallenge } from "./data/pathSolver.js";

const TYPE_LABELS = { team: "TEAM", player: "PLAYER", college: "COLLEGE", number: "NUMBER" };
const TYPE_COLORS = { team: "#dd2222", player: "#1177dd", college: "#bb7700", number: "#1a9944" };
const TYPE_BG = {
  team: "rgba(221,34,34,0.05)",
  player: "rgba(17,119,221,0.05)",
  college: "rgba(187,119,0,0.05)",
  number: "rgba(26,153,68,0.05)",
};
const TYPE_HINTS = {
  team: "Name a player who played on this team",
  player: "Name one of their teams, their college, or a jersey number",
  college: "Name a player who went to this school",
  number: "Name a player who wore this number",
};
const TYPE_EMOJI = { team: "🔴", player: "🔵", college: "🟡", number: "🟢" };

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

function Landing({ onFreePlay, onDaily, onRarity }) {
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
        <p className="tagline">Chain teams, players, colleges &amp; numbers.</p>
      </div>

      <div className="mode-buttons">
        <button className="mode-btn daily-btn" onClick={onDaily}>
          <div className="daily-kicker">
            <div className="daily-dot" />
            <span className="daily-kicker-label">DAILY CHALLENGE</span>
          </div>
          <div className="daily-card-route">
            <div className="daily-card-node">
              <div className="daily-card-label">START</div>
              <div className="daily-card-name">{daily.startName}</div>
            </div>
            <div className="daily-card-arrow">→</div>
            <div className="daily-card-node">
              <div className="daily-card-label">GOAL</div>
              <div className="daily-card-name">{daily.goalName}</div>
            </div>
          </div>
          <div className="daily-card-divider" />
          <div className="mode-btn-date">{daily.par} links · {today}</div>
        </button>

        <div className="mode-btn rarity-btn" onClick={() => onRarity(10)}>
          <div className="mode-btn-top">
            <span className="mode-btn-icon">💎</span>
            <span className="mode-btn-title">RARITY RUN</span>
          </div>
          <div className="mode-btn-desc">
            Build the rarest chain possible. Higher score = rarer links. Starting team is free.
          </div>
          <div className="rarity-options">
            <button onClick={(e) => { e.stopPropagation(); onRarity(5); }}>5 LINKS</button>
            <button onClick={(e) => { e.stopPropagation(); onRarity(10); }}>10 LINKS</button>
            <button onClick={(e) => { e.stopPropagation(); onRarity(20); }}>20 LINKS</button>
          </div>
        </div>

        <button className="mode-btn free-btn" onClick={onFreePlay}>
          <div className="mode-btn-title" style={{ marginBottom: 6 }}>Free play</div>
          <div className="mode-btn-desc">Pick any team. No limits.</div>
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
    </div>
  );
}

function Game({ onBack, modeType = "free", rarityLength = 10 }) {
  const dailyChallenge = modeType === "daily" ? getDailyLinkChallenge() : null;

  const isDaily = modeType === "daily";
  const isRarity = modeType === "rarity";
  const showPoints = isDaily || isRarity;

  const startName = isDaily ? dailyChallenge.startName : null;
  const startType = isDaily ? dailyChallenge.startType : null;
  const goalName = isDaily ? dailyChallenge.goalName : null;
  const goalType = isDaily ? dailyChallenge.goalType : null;

  const maxLinks = isRarity ? rarityLength : Infinity;

  const [phase, setPhase] = useState(isDaily ? "playing" : "start");
  const [history, setHistory] = useState(
    isDaily ? [{ name: startName, type: startType, points: 0 }] : []
  );
  const [currentItem, setCurrentItem] = useState(isDaily ? startName : null);
  const [currentType, setCurrentType] = useState(isDaily ? startType : null);
  const [input, setInput] = useState("");
  const [error, setError] = useState("");
  const [gameOver, setGameOver] = useState(false);
  const [wrongAnswer, setWrongAnswer] = useState(null);
  const [flash, setFlash] = useState(false);
  const [totalScore, setTotalScore] = useState(0);
  const [shared, setShared] = useState(false);
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

  const reachedGoal =
    isDaily &&
    history.length > 0 &&
    history[history.length - 1].type === goalType &&
    history[history.length - 1].name === goalName;

  const updateSuggestions = (value) => {
    const query = value.trim().toLowerCase();

    if (!query || query.length < 2) {
      setSuggestions([]);
      return;
    }

    let type = null;

    if (
      currentType === "team" ||
      currentType === "college" ||
      currentType === "number"
    ) {
      type = "player";
    }

    if (currentType === "player") {
      type = "college";
    }

    if (!type) {
      setSuggestions([]);
      return;
    }

    const options = getSuggestionOptions(type);

   const startsWithMatches = options.filter((option) =>
  option.toLowerCase().startsWith(query)
);

const includesMatches = options.filter((option) =>
  !option.toLowerCase().startsWith(query) &&
  option.toLowerCase().includes(query)
);

const matches = [
  ...startsWithMatches,
  ...includesMatches,
].slice(0, 8);

setSuggestions(matches);
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

      const reachedDailyGoal =
        isDaily &&
        type === goalType &&
        name === goalName;

      if (reachedDailyGoal) {
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
    if (isDaily) {
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

    const chain = history.map((h) => TYPE_EMOJI[h.type]).join("");

    let modeLabel = "Free Play";
    if (isDaily) modeLabel = "Daily Link";
    if (isRarity) modeLabel = `Rarity Run ${rarityLength}`;

    let text = `🔗 Sports Link ${modeLabel} — ${today}\n\n`;

    if (isDaily) {
      text += `${startName} → ${goalName}\n`;
    }

    text += `${chain}\n\n`;
    text += `${linksUsed} link${linksUsed !== 1 ? "s" : ""}`;

    if (showPoints) {
      text += ` · ${totalScore} pts`;
    }

    text += wrongAnswer ? " ❌" : " ✅";
    text += "\n\nsportslink1.vercel.app";

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

  const activeColor = currentType ? TYPE_COLORS[currentType] : "#ff4444";
  const activeBg = currentType ? TYPE_BG[currentType] : "transparent";

  if (gameOver) {
    const completed = !wrongAnswer && (reachedGoal || atLimit || modeType === "free");

    return (
      <div className="container">
        <div className="game-over-box">
          <div className="game-over-icon">
            {wrongAnswer ? "❌" : completed ? "🏆" : "🏁"}
          </div>

          <div className="game-over-title">
            {wrongAnswer ? "GAME OVER" : "COMPLETE!"}
          </div>

          {isDaily && (
            <div className="daily-challenge-box">
              <div className="daily-challenge-label">DAILY LINK</div>
              <div className="daily-challenge-route">
                <span className="daily-node start">{startName}</span>
                <span className="daily-arrow">→</span>
                <span className="daily-node goal">{goalName}</span>
              </div>
              <div className="daily-par">Par: {dailyChallenge.par}</div>
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
            <button className="btn-share" onClick={shareResult}>
              {shared ? "✓ COPIED!" : "📋 SHARE RESULT"}
            </button>
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
          {(isDaily || isRarity) && (
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

      {isDaily && (
        <div className="daily-challenge-box">
          <div className="daily-challenge-label">DAILY LINK</div>
          <div className="daily-challenge-route">
            <span className="daily-node start">{startName}</span>
            <span className="daily-arrow">→</span>
            <span className="daily-node goal">{goalName}</span>
          </div>
          <div className="daily-par">Par: {dailyChallenge.par}</div>
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
              className="game-input"
              autoComplete="off"
autoCorrect="off"
autoCapitalize="off"
spellCheck="false"
name="sports-link-input"
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

            <div className="hint">{TYPE_HINTS[currentType]}</div>
          </div>

          {history.length > 0 && (
            <History history={history} showPoints={showPoints} />
          )}

          {!atLimit && (
            <>
              <div className="input-row">
                <input
                  ref={inputRef}
                  className="game-input"
                  autoComplete="off"
autoCorrect="off"
autoCapitalize="off"
spellCheck="false"
name="sports-link-input"
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
  const [mode, setMode] = useState(null);
  const [rarityLength, setRarityLength] = useState(10);
  const [showTutorial, setShowTutorial] = useState(() => {
    return localStorage.getItem("sportsLinkTutorialSeen") !== "true";
  });

  function closeTutorial() {
    localStorage.setItem("sportsLinkTutorialSeen", "true");
    setShowTutorial(false);
  }

  useEffect(() => {
    async function testSupabase() {
      const { data, error } = await supabase
        .from("relationships")
        .select("*");

      console.log("SUPABASE DATA:", data);
      console.log("SUPABASE ERROR:", error);
    }

    testSupabase();
  }, []);

  if (mode === "free") {
    return <Game onBack={() => setMode(null)} modeType="free" />;
  }

  if (mode === "daily") {
    return <Game onBack={() => setMode(null)} modeType="daily" />;
  }

  if (mode === "rarity") {
    return (
      <Game
        onBack={() => setMode(null)}
        modeType="rarity"
        rarityLength={rarityLength}
      />
    );
  }

  return (
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
    />
  </div>
);
}
