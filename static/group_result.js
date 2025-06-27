const overlay = document.getElementById('overlay');
const btn = document.getElementById('next-team-btn');
const scheduleBtn = document.getElementById('schedule-btn'); // ✅ Khai báo đúng

const boxes = document.querySelectorAll('.group-box ul');
let idx = 0;
let groupIndex = 0;

const groups = JSON.parse(document.getElementById("groupdata").textContent);
const schedule = JSON.parse(document.getElementById("scheduledata").textContent);

// ✅ Vô hiệu hóa nút "Lịch thi đấu" ban đầu
scheduleBtn.disabled = true;

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

// Flatten team list
const teams = [];
Object.values(groups).forEach(group => {
  group.forEach(team => teams.push(team));
});

// Overlay ban đầu
overlay.style.display = 'block';
let firstClick = true;

btn.addEventListener('click', showNextTeam);

// ✅ Không cho bấm nếu chưa chia bảng xong
scheduleBtn.addEventListener("click", () => {
  if (idx < teams.length) {
    alert("⚠️ Bạn phải chia xong các đội trước khi hiển thị lịch thi đấu.");
    return;
  }
  console.log("🔔 Match schedule button clicked");
  generateSchedule();
});

async function showNextTeam() {
  if (idx >= teams.length) {
    btn.disabled = true;
    btn.textContent = "✅ Complete!";
    
    scheduleBtn.disabled = false;
    return;
  }

  if (firstClick) {
    overlay.style.display = 'none';
    firstClick = false;
  }

  const [tier1, tier2] = teams[idx];
  const box = boxes[groupIndex % boxes.length];

  await insertTeam(box, [tier1, tier2]);

  idx++;
  groupIndex++;
  setTimeout(showNextTeam, 1000);
}

function insertTeam(ul, team) {
  return new Promise((resolve) => {
    const allNames = teams.flatMap(t => t);
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

// ==============================
// MATCH SCHEDULE HIỂN THỊ NGAY
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

      // Format đẹp: dùng span căn chỉnh rõ ràng
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
}

function roundRobin(teams) {
  const result = [];
  const n = teams.length;
  const isOdd = n % 2 !== 0;
  const list = teams.slice();

  if (isOdd) list.push(["BYE", ""]);

  const totalRounds = list.length - 1;
  for (let round = 0; round < totalRounds; round++) {
    for (let i = 0; i < list.length / 2; i++) {
      const t1 = list[i];
      const t2 = list[list.length - 1 - i];
      if (t1[0] !== "BYE" && t2[0] !== "BYE") {
        result.push([
          `${t1[0]} – ${t1[1]}`,
          `${t2[0]} – ${t2[1]}`
        ]);
      }
    }
    const last = list.pop();
    list.splice(1, 0, last);
  }
  return result;
}
