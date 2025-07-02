// 🔁 Hình nền luân phiên
const bgImages = [
  "/static/background1.jpg",
  "/static/background2.jpg",
  "/static/background3.jpg"
];

let currentBg = 0;
let visibleLayer = 0;

function switchBackground() {
  const nextBg = (currentBg + 1) % bgImages.length;
  const showId = visibleLayer === 0 ? 'bg2' : 'bg1';
  const hideId = visibleLayer === 0 ? 'bg1' : 'bg2';

  const show = document.getElementById(showId);
  const hide = document.getElementById(hideId);

  show.style.backgroundImage = `url('${bgImages[nextBg]}')`;
  show.classList.add('active');
  hide.classList.remove('active');

  currentBg = nextBg;
  visibleLayer = 1 - visibleLayer;
}

// ✅ Hiện ảnh đầu tiên khi tải trang
document.getElementById("bg1").style.backgroundImage = `url('${bgImages[0]}')`;
document.getElementById("bg1").classList.add("active");
setInterval(switchBackground, 12000);

// ✅ Xử lý nhập tỉ số không reload
document.querySelectorAll('.score-input').forEach((input, index, inputs) => {
  input.addEventListener('change', () => {
    const matchId = input.dataset.id;
    const pair = [...inputs].filter(i => i.dataset.id === matchId);
    if (pair.length !== 2) return;

    const s1 = parseInt(pair[0].value);
    const s2 = parseInt(pair[1].value);

    if (isNaN(s1) || isNaN(s2)) return;
    if (s1 === s2 && input.closest("table")?.classList.contains("knockout")) {
      alert("Không được hòa trong vòng knock-out");
      return;
    }

    const matchBox = input.closest(".match-box") || input.closest("tr");
    matchBox?.classList.add('loading');

    fetch("/update_score", {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        match_id: matchId,
        score1: s1,
        score2: s2
      })
    })
    .then(res => res.json())
    .then(data => {
    matchBox?.classList.remove('loading');

    if (data.status === "ok") {
        if (data.standings && data.group_id) {
        updateStandingsTable(data.group_id, data.standings);
        } else if (data.updated === "knockout") {
        if (data.updated_matches) {
            updateKnockoutDOM(data.updated_matches);
            
        }
        if (data.final_ranking && data.champion) {
            updateFinalRanking(data.final_ranking, data.champion);
        }
        }
    } else {
        alert("Lỗi khi cập nhật tỉ số.");
    }
    })
    .catch(err => {
      matchBox?.classList.remove('loading');
      alert("Lỗi kết nối máy chủ.");
      console.error(err);
    });
  });
});
function updateFinalRanking(ranking, championName) {
  if (!Array.isArray(ranking)) return;

  // ✅ Cập nhật bảng xếp hạng
  const table = document.querySelector(".final-ranking tbody");
  if (table) {
    table.innerHTML = "";
    ranking.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${row.rank}</td><td>${row.name}</td>`;
      table.appendChild(tr);
    });
  }

  // ✅ Hiển thị overlay đội vô địch
  const overlay = document.getElementById("champion-overlay");
  const nameElem = document.getElementById("overlay-champion-name");

  // Debug tạm
  console.log("⚠️ championName từ backend:", championName);
  console.log("✅ DOM overlay:", overlay);
  console.log("✅ DOM nameElem:", nameElem);

  if (overlay && nameElem && championName) {
    nameElem.textContent = championName.toUpperCase(); // viết hoa toàn bộ

    overlay.style.display = "flex";

    launchFireworks(); // canvas-confetti

    setTimeout(() => {
      overlay.style.display = "none";
    }, 6000);
  }
}

// ✅ Cập nhật tên đội và tỉ số các trận knock-out
function updateKnockoutDOM(updatedMatches) {
  updatedMatches.forEach(match => {
    const inputs = document.querySelectorAll(`.score-input[data-id='${match.id}']`);
    const row = inputs[0]?.closest("tr");
    if (!row) return;

    // Ưu tiên cập nhật bằng class để tránh sai vị trí
    const team1Cell = row.querySelector(".team1");
    const team2Cell = row.querySelector(".team2");
    if (team1Cell) team1Cell.innerText = match.team1 || '';
    if (team2Cell) team2Cell.innerText = match.team2 || '';

    if (inputs.length === 2) {
      inputs[0].value = match.score1 !== null ? match.score1 : '';
      inputs[1].value = match.score2 !== null ? match.score2 : '';
    }
  });
}
function launchFireworks() {
  const canvas = document.getElementById("confetti-canvas");
  const myConfetti = confetti.create(canvas, { resize: true, useWorker: true });

  const duration = 5000;
  const end = Date.now() + duration;

  const defaults = {
    origin: { y: 0.7 },
    colors: ['#facc15', '#f59e0b', '#f87171', '#60a5fa', '#34d399', '#eab308', '#ef4444'],
    scalar: 1.2,
    ticks: 250,
    zIndex: 9999
  };

  const interval = setInterval(() => {
    if (Date.now() > end) {
      clearInterval(interval);
      return;
    }

    myConfetti({ ...defaults, particleCount: 60, spread: 80, angle: 60, origin: { x: 0 } });
    myConfetti({ ...defaults, particleCount: 60, spread: 80, angle: 120, origin: { x: 1 } });
    myConfetti({ ...defaults, particleCount: 40, spread: 160, origin: { x: Math.random(), y: Math.random() * 0.5 } });
  }, 250);
}
