const state = {
  generatedCount: 0,
  showSolutions: false,
  currentExam: null,
  profile: null,
  timerHandle: null,
  timerRemainingSec: 0,
};

const subjectEl = document.getElementById("subject");
const modeEl = document.getElementById("mode");
const levelEl = document.getElementById("level");
const generateBtn = document.getElementById("generateBtn");
const examTitleEl = document.getElementById("examTitle");
const tasksEl = document.getElementById("tasks");
const setCountEl = document.getElementById("setCount");
const totalPointsEl = document.getElementById("totalPoints");
const minutesEl = document.getElementById("minutes");
const toggleSolutionsBtn = document.getElementById("toggleSolutionsBtn");
const scoreBtn = document.getElementById("scoreBtn");
const scoreSummaryEl = document.getElementById("scoreSummary");
const startMockBtn = document.getElementById("startMockBtn");
const timerEl = document.getElementById("timer");
const pdfBtn = document.getElementById("pdfBtn");
const profileNameViewEl = document.getElementById("profileNameView");
const overallPercentEl = document.getElementById("overallPercent");
const profileNameEl = document.getElementById("profileName");
const targetYearEl = document.getElementById("targetYear");
const streakEl = document.getElementById("streak");
const saveProfileBtn = document.getElementById("saveProfileBtn");
const refreshPastBtn = document.getElementById("refreshPastBtn");
const pastExamsEl = document.getElementById("pastExams");

const formatTimer = (seconds) => {
  const min = Math.floor(seconds / 60);
  const sec = seconds % 60;
  return `${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
};

const updateTimerUI = () => {
  timerEl.textContent = formatTimer(Math.max(0, state.timerRemainingSec));
};

const startTimer = (minutes) => {
  if (state.timerHandle) {
    clearInterval(state.timerHandle);
  }
  state.timerRemainingSec = minutes * 60;
  updateTimerUI();
  state.timerHandle = setInterval(() => {
    state.timerRemainingSec -= 1;
    updateTimerUI();
    if (state.timerRemainingSec <= 0) {
      clearInterval(state.timerHandle);
      state.timerHandle = null;
      alert("Lejárt az időd a próbaérettségin!");
    }
  }, 1000);
};

const escapeHtml = (text) =>
  String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

const renderTasks = (exam) => {
  state.currentExam = exam;
  const isOral = exam.mode === "szobeli";
  examTitleEl.textContent = exam.title;
  const totalPoints = exam.tasks.reduce((sum, t) => sum + (t.max_points || 0), 0);
  totalPointsEl.textContent = isOral ? "szóbeli" : String(totalPoints);
  minutesEl.textContent = `${exam.estimated_minutes} perc`;
  setCountEl.textContent = String(state.generatedCount);

  tasksEl.classList.toggle("show-solutions", state.showSolutions);
  tasksEl.innerHTML = exam.tasks
    .map((task, idx) => {
      const pointLabel = task.max_points > 0 ? `${task.max_points} pont` : "szóbeli";
      const answerLabel = isOral
        ? "Vázlat / jegyzeteid a feleletedhez..."
        : "Ide írd a válaszodat...";
      const solutionLabel = isOral ? "Elvárás / értékelési szempont" : "Mintamegoldás";
      return `
      <article class="task">
        <div class="task-head">
          <div>
            <h3>${idx + 1}. ${escapeHtml(task.title)}</h3>
            <span class="pill">${escapeHtml(task.topic)}</span>
          </div>
          <strong>${pointLabel}</strong>
        </div>
        <p>${escapeHtml(task.prompt)}</p>
        <textarea class="answer-box" data-answer-index="${idx}" placeholder="${answerLabel}"></textarea>
        <div class="meta"><strong>Tipp:</strong> ${escapeHtml(task.hint)}</div>
        <div class="meta"><strong>Forrás:</strong> ${escapeHtml(task.source)}</div>
        <div class="solution"><strong>${solutionLabel}:</strong> ${escapeHtml(task.sample_solution)}</div>
      </article>
    `;
    })
    .join("");
};

const getAnswers = () =>
  Array.from(document.querySelectorAll(".answer-box")).map((el) => el.value.trim());

const scoreCurrentExam = async () => {
  if (!state.currentExam) return;
  try {
    const response = await fetch("/api/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        exam: state.currentExam,
        answers: getAnswers(),
      }),
    });
    if (!response.ok) throw new Error("Pontozás sikertelen.");
    const result = await response.json();
    scoreSummaryEl.classList.remove("hidden");
    const header =
      result.max_total > 0
        ? `<strong>Eredmény: ${result.earned_total} / ${result.max_total} pont (${result.percentage}%)</strong>
           <p>${result.percentage >= 70 ? "Nagyon jó haladás!" : "Még van tér fejlődni, gyakorolj tovább."}</p>`
        : `<strong>Szóbeli gyakorlat – az alábbi részletes visszajelzést nézd át.</strong>`;
    scoreSummaryEl.innerHTML = header + renderAnalysisHtml(result.analysis, false);
    await loadProfile();
  } catch (error) {
    scoreSummaryEl.classList.remove("hidden");
    scoreSummaryEl.textContent = `Hiba: ${error.message}`;
  }
};

const exportPdf = async () => {
  if (!state.currentExam) return;
  const response = await fetch("/api/export/pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ exam: state.currentExam }),
  });
  if (!response.ok) {
    alert("Nem sikerült a PDF export.");
    return;
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "erettsegi_feladatsor.pdf";
  anchor.click();
  URL.revokeObjectURL(url);
};

const SUBJECT_LABELS = {
  matek: "Matek",
  irodalom: "Irodalom",
  tortenelem: "Történelem",
  nemet: "Német",
};

const charts = { overall: null, subject: null };

const computeOverall = (profile) =>
  Object.values(profile.subject_stats || {}).reduce(
    (acc, stat) => {
      acc.max += stat.max || 0;
      acc.earned += stat.earned || 0;
      return acc;
    },
    { max: 0, earned: 0 }
  );

const updateCharts = (profile) => {
  if (typeof Chart === "undefined") return;

  const overall = computeOverall(profile);
  const earned = overall.earned;
  const remaining = Math.max(overall.max - overall.earned, 0);

  if (charts.overall) {
    charts.overall.data.datasets[0].data = [earned, remaining];
    charts.overall.update();
  } else {
    charts.overall = new Chart(document.getElementById("overallChart"), {
      type: "doughnut",
      data: {
        labels: ["Megszerzett pont", "Hátralévő"],
        datasets: [
          {
            data: [earned, remaining],
            backgroundColor: ["#ff3b57", "#3a1418"],
            borderColor: "#150406",
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#c89aa0" } } },
      },
    });
  }

  const keys = Object.keys(SUBJECT_LABELS);
  const percents = keys.map((key) => {
    const stat = (profile.subject_stats || {})[key] || { earned: 0, max: 0 };
    return stat.max ? Math.round((stat.earned / stat.max) * 1000) / 10 : 0;
  });

  if (charts.subject) {
    charts.subject.data.datasets[0].data = percents;
    charts.subject.update();
  } else {
    charts.subject = new Chart(document.getElementById("subjectChart"), {
      type: "bar",
      data: {
        labels: keys.map((key) => SUBJECT_LABELS[key]),
        datasets: [
          {
            label: "Pontszázalék (%)",
            data: percents,
            backgroundColor: "#e02440",
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true, max: 100, ticks: { color: "#c89aa0" }, grid: { color: "#2a1014" } },
          x: { ticks: { color: "#c89aa0" }, grid: { display: false } },
        },
        plugins: { legend: { labels: { color: "#c89aa0" } } },
      },
    });
  }
};

const renderProfile = (profile) => {
  state.profile = profile;
  profileNameEl.value = profile.name || "";
  targetYearEl.value = profile.target_year || 2027;
  streakEl.value = profile.streak_days || 0;
  profileNameViewEl.textContent = profile.name || "Diák";
  const overall = computeOverall(profile);
  const percent = overall.max ? ((overall.earned / overall.max) * 100).toFixed(1) : "0.0";
  overallPercentEl.textContent = `${percent}%`;
  updateCharts(profile);
};

const loadProfile = async () => {
  const response = await fetch("/api/profile");
  if (!response.ok) return;
  const profile = await response.json();
  renderProfile(profile);
};

const saveProfile = async () => {
  const response = await fetch("/api/profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: profileNameEl.value.trim(),
      target_year: Number(targetYearEl.value),
      streak_days: Number(streakEl.value),
    }),
  });
  if (!response.ok) {
    alert("Profil mentés sikertelen.");
    return;
  }
  const profile = await response.json();
  renderProfile(profile);
};

const loadPastExams = async () => {
  pastExamsEl.innerHTML = `<p class="empty">Betöltés folyamatban...</p>`;
  const response = await fetch("/api/past-exams");
  if (!response.ok) {
    pastExamsEl.innerHTML = `<p class="empty">Nem sikerült lekérni az Oktatási Hivatal listát.</p>`;
    return;
  }
  const data = await response.json();
  if (!data.items || !data.items.length) {
    pastExamsEl.innerHTML = `<p class="empty">Most nem érhető el lista. Később frissítsd újra.</p>`;
    return;
  }
  pastExamsEl.innerHTML = data.items
    .slice(0, 12)
    .map(
      (item) =>
        `<article class="task"><a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.title}</a></article>`
    )
    .join("");
};

const generateExam = async () => {
  generateBtn.disabled = true;
  generateBtn.textContent = "Generálás...";
  try {
    const params = new URLSearchParams({
      subject: subjectEl.value,
      mode: modeEl.value,
      level: levelEl.value,
    });
    const response = await fetch(`/api/exam?${params.toString()}`);
    if (!response.ok) {
      throw new Error("Nem sikerült lekérni a feladatsort.");
    }
    const exam = await response.json();
    state.generatedCount += 1;
    scoreSummaryEl.classList.add("hidden");
    scoreSummaryEl.textContent = "";
    renderTasks(exam);
    await loadProfile();
  } catch (error) {
    tasksEl.innerHTML = `<p class="empty">Hiba: ${error.message}</p>`;
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "Feladatsor generálása";
  }
};

toggleSolutionsBtn.addEventListener("click", () => {
  state.showSolutions = !state.showSolutions;
  tasksEl.classList.toggle("show-solutions", state.showSolutions);
  toggleSolutionsBtn.textContent = state.showSolutions
    ? "Mintamegoldások elrejtése"
    : "Mintamegoldások mutatása";
});

const renderAnalysisHtml = (analysis, isOral) => {
  if (!analysis) return "";
  const m = analysis.metrics || {};
  const metricCards = [];
  metricCards.push(
    `<div class="metric"><span>Tartalmi lefedettség</span><strong>${m.coverage_percent ?? 0}%</strong></div>`
  );
  metricCards.push(
    `<div class="metric"><span>Szókincs gazdagsága</span><strong>${m.vocab_richness_percent ?? 0}%</strong></div>`
  );
  metricCards.push(`<div class="metric"><span>Szavak száma</span><strong>${m.word_count ?? 0}</strong></div>`);
  if (isOral) {
    metricCards.push(
      `<div class="metric"><span>Beszédtempó</span><strong>${m.speaking_rate_wpm ?? 0} szó/p</strong></div>`
    );
    metricCards.push(
      `<div class="metric"><span>Tétovázás a kezdésnél</span><strong>${m.first_word_delay_sec ?? 0} mp</strong></div>`
    );
    metricCards.push(
      `<div class="metric"><span>Hosszú szünetek</span><strong>${m.long_pause_count ?? 0}</strong></div>`
    );
  }

  const recs = (analysis.recommendations || [])
    .map((r) => `<li>${escapeHtml(r)}</li>`)
    .join("");
  const strengths = (analysis.strengths || [])
    .map((s) => `<li>${escapeHtml(s)}</li>`)
    .join("");

  return `
    <div class="metric-grid">${metricCards.join("")}</div>
    ${strengths ? `<h4>Erősségek</h4><ul class="good">${strengths}</ul>` : ""}
    ${recs ? `<h4>Min fejlődj?</h4><ul>${recs}</ul>` : ""}
  `;
};

// ----- Élő szóbeli vizsga (Web Speech API) -----
const oralStartBtn = document.getElementById("oralStartBtn");
const oralStopBtn = document.getElementById("oralStopBtn");
const oralStatusEl = document.getElementById("oralStatus");
const oralLiveEl = document.getElementById("oralLive");
const oralTimerEl = document.getElementById("oralTimer");
const oralTicketEl = document.getElementById("oralTicket");
const oralTranscriptEl = document.getElementById("oralTranscript");
const oralAnalysisEl = document.getElementById("oralAnalysis");
const oralRecStateEl = document.getElementById("oralRecState");

const ORAL_DURATION_SEC = 15 * 60;
const LONG_PAUSE_MS = 4000;

const oral = {
  recognition: null,
  active: false,
  timerHandle: null,
  remaining: ORAL_DURATION_SEC,
  exam: null,
  finalTranscript: "",
  startMs: 0,
  firstWordMs: 0,
  lastResultMs: 0,
  longPauseCount: 0,
  silenceMs: 0,
};

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const buildTicketHtml = (exam) => {
  const parts = exam.tasks
    .map(
      (t, i) => `
      <div class="part">
        <strong>${i + 1}. ${escapeHtml(t.title)}</strong>
        <p>${escapeHtml(t.prompt)}</p>
      </div>`
    )
    .join("");
  return `<h3>Kihúzott tétel — ${escapeHtml(exam.subject_label)} (${escapeHtml(exam.mode_label)})</h3>${parts}`;
};

const expectedTextFromExam = (exam) =>
  exam.tasks
    .map((t) => `${t.title} ${t.topic} ${t.sample_solution} ${t.hint}`)
    .join(" ");

const formatMMSS = (sec) => {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
};

const stopOralExam = async () => {
  if (!oral.active) return;
  oral.active = false;
  if (oral.timerHandle) clearInterval(oral.timerHandle);
  if (oral.recognition) {
    try {
      oral.recognition.stop();
    } catch (e) {
      /* ignore */
    }
  }
  oralRecStateEl.textContent = "■ leállítva";
  oralStartBtn.disabled = false;
  oralStopBtn.disabled = true;

  const elapsed = (Date.now() - oral.startMs) / 1000;
  const firstDelay = oral.firstWordMs ? (oral.firstWordMs - oral.startMs) / 1000 : elapsed;

  oralAnalysisEl.classList.remove("hidden");
  oralAnalysisEl.innerHTML = "<strong>Elemzés folyamatban...</strong>";

  try {
    const response = await fetch("/api/analyze-oral", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        subject: oral.exam.subject,
        transcript: oral.finalTranscript,
        expected_text: expectedTextFromExam(oral.exam),
        duration_sec: elapsed,
        first_word_delay_sec: firstDelay,
        long_pause_count: oral.longPauseCount,
        silence_sec: oral.silenceMs / 1000,
      }),
    });
    if (!response.ok) throw new Error("Elemzés sikertelen.");
    const analysis = await response.json();
    oralAnalysisEl.innerHTML =
      `<strong>Szóbeli elemzés kész</strong>` + renderAnalysisHtml(analysis, true);
    await loadProfile();
  } catch (error) {
    oralAnalysisEl.innerHTML = `<strong>Hiba:</strong> ${escapeHtml(error.message)}`;
  }
};

const startOralExam = async () => {
  if (!SpeechRecognition) {
    oralStatusEl.textContent =
      "Ez a böngésző nem támogatja a beszédfelismerést. Használj Google Chrome vagy Microsoft Edge böngészőt.";
    return;
  }

  oralStartBtn.disabled = true;
  oralAnalysisEl.classList.add("hidden");
  oralAnalysisEl.innerHTML = "";

  try {
    const params = new URLSearchParams({
      subject: subjectEl.value,
      mode: "szobeli",
      level: levelEl.value,
    });
    const response = await fetch(`/api/exam?${params.toString()}`);
    if (!response.ok) throw new Error("Nem sikerült tételt húzni.");
    oral.exam = await response.json();
  } catch (error) {
    oralStatusEl.textContent = `Hiba: ${error.message}`;
    oralStartBtn.disabled = false;
    return;
  }

  oral.active = true;
  oral.finalTranscript = "";
  oral.startMs = Date.now();
  oral.firstWordMs = 0;
  oral.lastResultMs = oral.startMs;
  oral.longPauseCount = 0;
  oral.silenceMs = 0;
  oral.remaining = ORAL_DURATION_SEC;

  oralLiveEl.classList.remove("hidden");
  oralTicketEl.innerHTML = buildTicketHtml(oral.exam);
  oralTranscriptEl.innerHTML = "";
  oralTimerEl.textContent = formatMMSS(oral.remaining);
  oralRecStateEl.textContent = "● felvétel";
  oralStopBtn.disabled = false;

  const recognition = new SpeechRecognition();
  recognition.lang = oral.exam.subject === "nemet" ? "de-DE" : "hu-HU";
  recognition.continuous = true;
  recognition.interimResults = true;

  recognition.onresult = (event) => {
    const now = Date.now();
    if (!oral.firstWordMs) oral.firstWordMs = now;
    const gap = now - oral.lastResultMs;
    if (gap > LONG_PAUSE_MS) {
      oral.longPauseCount += 1;
      oral.silenceMs += gap;
    }
    oral.lastResultMs = now;

    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const chunk = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        oral.finalTranscript += chunk + " ";
      } else {
        interim += chunk;
      }
    }
    oralTranscriptEl.innerHTML =
      escapeHtml(oral.finalTranscript) + `<span class="interim">${escapeHtml(interim)}</span>`;
    oralTranscriptEl.scrollTop = oralTranscriptEl.scrollHeight;
  };

  recognition.onerror = (event) => {
    if (event.error === "not-allowed" || event.error === "service-not-allowed") {
      oralStatusEl.textContent = "A mikrofon-hozzáférés le lett tiltva. Engedélyezd a böngészőben!";
    }
  };

  recognition.onend = () => {
    // Ha még aktív (nem a diák állította le), indítsuk újra a folyamatos felvételhez.
    if (oral.active) {
      try {
        recognition.start();
      } catch (e) {
        /* ignore */
      }
    }
  };

  oral.recognition = recognition;
  try {
    recognition.start();
  } catch (e) {
    /* ignore */
  }

  oral.timerHandle = setInterval(() => {
    oral.remaining -= 1;
    oralTimerEl.textContent = formatMMSS(Math.max(0, oral.remaining));
    if (oral.remaining <= 0) {
      stopOralExam();
    }
  }, 1000);
};

if (oralStartBtn) {
  oralStartBtn.addEventListener("click", startOralExam);
  oralStopBtn.addEventListener("click", stopOralExam);
}

generateBtn.addEventListener("click", generateExam);
scoreBtn.addEventListener("click", scoreCurrentExam);
startMockBtn.addEventListener("click", () => {
  if (!state.currentExam) return;
  startTimer(state.currentExam.estimated_minutes);
});
pdfBtn.addEventListener("click", exportPdf);
saveProfileBtn.addEventListener("click", saveProfile);
refreshPastBtn.addEventListener("click", loadPastExams);

loadProfile();
loadPastExams();
generateExam();
