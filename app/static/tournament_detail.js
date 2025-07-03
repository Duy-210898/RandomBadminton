// 🔁 Đổi hình nền định kỳ
const bgImages = [
  "/static/background1.jpg",
  "/static/background2.jpg",
  "/static/background3.jpg"
];

let currentBg = 0;
let visibleLayer = 0;

function switchBackground() {
  const nextBg = (currentBg + 1) % bgImages.length;
  const showLayer = visibleLayer === 0 ? 'bg2' : 'bg1';
  const hideLayer = visibleLayer === 0 ? 'bg1' : 'bg2';

  const show = document.getElementById(showLayer);
  const hide = document.getElementById(hideLayer);

  show.style.backgroundImage = `url(${bgImages[nextBg]})`;
  show.classList.add('active');
  hide.classList.remove('active');

  currentBg = nextBg;
  visibleLayer = 1 - visibleLayer;
}

// ✅ Khởi động: hiện ảnh đầu tiên
document.getElementById("bg1").style.backgroundImage = `url(${bgImages[0]})`;
document.getElementById("bg1").classList.add("active");

// ⏱️ Đổi ảnh mỗi 12 giây
setInterval(switchBackground, 12000);


document.querySelectorAll('.score-input').forEach((input, index, inputs) => {
  input.addEventListener('change', () => {
    const id = input.dataset.id;
    const pair = [...inputs].filter(i => i.dataset.id === id);
    const s1 = parseInt(pair[0].value);
    const s2 = parseInt(pair[1].value);

    const matchBox = input.closest('.match-box');
    matchBox?.classList.add('loading'); // 👉 Show loading spinner

    if (!isNaN(s1) && !isNaN(s2)) {
      fetch("/update_score", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          match_id: id,
          score1: s1,
          score2: s2
        })
      })
      .then(res => res.json())
      .then(data => {
        matchBox?.classList.remove('loading'); // ✅ Hide loading spinner

        if (data.status === "ok" && data.standings) {
          updateStandingsTable(data.group_id, data.standings);
        } else {
          location.reload();
        }
      });
    }
  });
});

function updateStandingsTable(groupId, standings) {
  const table = document.querySelector(`table[data-group-id='${groupId}']`);
  if (!table) return;

  const tbody = table.querySelector("tbody");
  tbody.innerHTML = "";

  standings.team_rows.forEach((team, index) => {
    const tr = document.createElement("tr");
    let html = `<td>${team.name}</td>`;
    html += team.match_points.map(p => `<td>${p}</td>`).join('');
    html += `<td>${team.total_points}</td><td>${team.gd}</td>`;
    tr.innerHTML = html;
    if (index === 0) tr.classList.add('top-team');  // ✅ Highlight đội đầu bảng
    tbody.appendChild(tr);
  });
}
