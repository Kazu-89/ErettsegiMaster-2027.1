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
    scoreSummaryEl.innerHTML = `
      <strong>Eredmény: ${result.earned_total} / ${result.max_total} pont (${result.percentage}%)</strong>
      <p>${result.percentage >= 70 ? "Nagyon jó haladás!" : "Még van tér fejlődni, gyakorolj tovább."}</p>
    `;
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
