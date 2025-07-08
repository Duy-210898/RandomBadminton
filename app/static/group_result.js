const overlay = document.getElementById('overlay');
const btn = document.getElementById('next-team-btn');
const scheduleBtn = document.getElementById('schedule-btn');

const boxes = document.querySelectorAll('.group-box ul');

const groups = JSON.parse(document.getElementById("groupdata").textContent);
const schedule = JSON.parse(document.getElementById("scheduledata").textContent);

// ✅ DỮ LIỆU nhóm đội (group name + list đội)
const groupedTeams = Object.entries(groups);  // [ [groupName, [ [tier1, tier2], ... ]], ... ]
let groupIndex = 0;
let teamIndex = 0;
let isComplete = false;

scheduleBtn.disabled = true;

// ======================
// BACKGROUND CROSSFADE
// ======================
const bgImages = [
  "/static/background1.jpg",
  "/static/background2.jpg",
  "/static/background3.jpg"
];
let currentIndex = 0;
let activeLayer = 1;

function crossfadeBackground() {
  const nextIndex = (currentIndex + 1) % bgImages.length;
  const topLayerId = activeLayer === 1 ? "bg2" : "bg1";
  const bottomLayerId = activeLayer === 1 ? "bg1" : "bg2";

  const topLayer = document.getElementById(topLayerId);
  const bottomLayer = document.getElementById(bottomLayerId);

  topLayer.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('${bgImages[nextIndex]}')`;
  topLayer.style.opacity = "1";
  bottomLayer.style.opacity = "0";

  activeLayer = activeLayer === 1 ? 2 : 1;
  currentIndex = nextIndex;
}
setInterval(crossfadeBackground, 10000);

// ======================
// SỰ KIỆN NÚT
// ======================
overlay.style.display = 'block';
let firstClick = true;

btn.addEventListener('click', showNextTeam);
scheduleBtn.addEventListener('click', () => {
  if (!isComplete) {
    alert("⚠️ Bạn phải chia xong các đội trước khi hiển thị lịch thi đấu.");
    return;
  }
  generateSchedule();
});

// ======================
// HIỂN THỊ ĐỘI TIẾP THEO
// ======================
async function showNextTeam() {
  if (isComplete || btn.disabled) return;

  btn.disabled = true;

  if (firstClick) {
    overlay.style.display = 'none';
    firstClick = false;
  }

  const [groupName, teamList] = groupedTeams[groupIndex];
  const box = boxes[groupIndex];

  if (teamIndex < teamList.length) {
    const [tier1, tier2] = teamList[teamIndex];
    await insertTeam(box, [tier1, tier2]);
    teamIndex++;

    // ✅ Kiểm tra hoàn tất **sau khi xử lý đội cuối**
    if (
      groupIndex === groupedTeams.length - 1 &&
      teamIndex === teamList.length
    ) {
      btn.disabled = true;
      btn.textContent = "✅ Complete!";
      scheduleBtn.disabled = false;
      isComplete = true;
      return;
    }

    setTimeout(() => {
      btn.disabled = false;
      showNextTeam(); // Tự động tiếp tục
    }, 1000);
  } else {
    // chuyển sang nhóm kế tiếp
    groupIndex++;
    teamIndex = 0;
    btn.disabled = false;
    showNextTeam(); // tiếp tục nhóm mới
  }
}

// ======================
// HIỆU ỨNG HIỂN THỊ TỪNG ĐỘI
// ======================
function insertTeam(ul, team) {
  return new Promise((resolve) => {
    const allNames = groupedTeams.flatMap(g => g[1]).flatMap(t => t);
    const totalFrames = 35;
    const li = document.createElement('li');
    li.className = 'team-effect';
    li.style.opacity = '0';
    ul.appendChild(li);

    let frame = 0;

    function animate() {
      const progress = frame / totalFrames;
      const delay = easeOutCubic(progress) * 120;
      const f1 = allNames[Math.floor(Math.random() * allNames.length)];
      const f2 = allNames[Math.floor(Math.random() * allNames.length)];
      li.textContent = `${f1} – ${f2}`;
      li.style.opacity = '1';
      li.classList.remove('reveal');
      li.style.transform = `scale(${1 + Math.random() * 0.05})`;
      frame++;

      if (frame < totalFrames) {
        setTimeout(() => requestAnimationFrame(animate), delay);
      } else {
        li.textContent = `${team[0]} – ${team[1]}`;
        li.classList.add('reveal', 'team-show');
        li.style.transform = 'scale(1.2)';
        try {
          confetti({ particleCount: 100, spread: 90, origin: { y: 0.6 } });
        } catch (e) {
          console.warn("Confetti error:", e);
        }
        setTimeout(() => {
          li.style.transform = 'scale(1)';
          resolve();
        }, 300);
      }
    }

    requestAnimationFrame(animate);
  });
}

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3);
}
document.getElementById("add-team-btn").addEventListener("click", () => {
  const groupName = document.getElementById("group-select").value;
  const tier1 = document.getElementById("tier1-name").value.trim();
  const tier2 = document.getElementById("tier2-name").value.trim();

  if (!tier1 || !tier2) {
    alert("⚠️ Vui lòng nhập đầy đủ tên 2 đội.");
    return;
  }

  const groupIndex = groupedTeams.findIndex(g => g[0] === groupName);
  if (groupIndex === -1) {
    alert(`❌ Bảng ${groupName} không tồn tại.`);
    return;
  }

  const teamList = groupedTeams[groupIndex][1];
  teamList.push([tier1, tier2]);

  // Hiển thị lên đúng bảng
  const boxes = document.querySelectorAll('.group-box ul');
  const box = boxes[groupIndex];

  // Dùng lại hiệu ứng insertTeam
  insertTeam(box, [tier1, tier2]);

  // Reset input
  document.getElementById("tier1-name").value = "";
  document.getElementById("tier2-name").value = "";

  alert(`✅ Đã thêm cặp: ${tier1} – ${tier2} vào bảng ${groupName}`);
});

// ==============================
// HIỂN THỊ LỊCH THI ĐẤU VÒNG BẢNG
// ==============================
function generateSchedule() {
  const container = document.getElementById("schedule-tables");
  container.innerHTML = "";
  document.getElementById("schedule-container").style.display = "block";

  for (const groupName in schedule) {
    const matches = schedule[groupName];

    const box = document.createElement("div");
    box.className = "schedule-box";

    const title = document.createElement("h2");
    title.textContent = groupName;
    box.appendChild(title);

    const ul = document.createElement("ul");
    matches.forEach(([team1, team2], index) => {
      const li = document.createElement("li");

      li.innerHTML = `
        <span class="match-number">Trận ${index + 1}:</span>
        <span class="match-team">${team1}</span>
        <span class="vs">🆚</span>
        <span class="match-team">${team2}</span>
      `;

      ul.appendChild(li);
    });

    box.appendChild(ul);
    container.appendChild(box);
  }

  scheduleBtn.disabled = true;
  btn.disabled = true;

  // ✅ Hiển thị nút NEXT ROUND khi đã hiện lịch thi đấu
  const nextRoundBtn = document.getElementById("next-round-container");
  if (nextRoundBtn) {
    nextRoundBtn.style.display = "block";
  }
}
