document.addEventListener("DOMContentLoaded", () => {
  const slot1 = document.getElementById("tier1-slot");
  const slot2 = document.getElementById("tier2-slot");
  const popup = document.getElementById("popup-team");
  const overlay = document.getElementById("overlay");
  const teamList = document.getElementById("team-list");
  const startBtn = document.getElementById("start-btn");
  const container = document.getElementById("fireworks-container");

  let index = 0, processing = false;

  const teams = JSON.parse(document.getElementById("teams-data").textContent);
  const bgImages = [
    "/static/background1.jpg",
    "/static/background2.jpg",
    "/static/background3.jpg"
  ];

  let currentIndex = 0;
  let activeLayer = 1;

  function crossfadeBackground() {
    const nextIndex = (currentIndex + 1) % bgImages.length;
    const nextImage = bgImages[nextIndex];

    const topLayerId = activeLayer === 1 ? "bg2" : "bg1";
    const bottomLayerId = activeLayer === 1 ? "bg1" : "bg2";

    const topLayer = document.getElementById(topLayerId);
    const bottomLayer = document.getElementById(bottomLayerId);

    topLayer.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('${nextImage}')`;
    topLayer.style.opacity = "1";
    bottomLayer.style.opacity = "0";

    activeLayer = activeLayer === 1 ? 2 : 1;
    currentIndex = nextIndex;
  }

  setInterval(crossfadeBackground, 10000);

  if (typeof Fireworks !== "undefined" && container) {
    window.fireworks = new Fireworks(container, {
      rocketsPoint: { min: 0, max: 100 },
      hue: { min: 0, max: 360 },
      delay: { min: 2, max: 5 },
      speed: 6,
      acceleration: 1.1,
      friction: 0.92,
      gravity: 2.0,
      particles: 800,
      trace: 14,
      explosion: 10,
      autoresize: true,
      brightness: { min: 85, max: 100, decay: { min: 0.004, max: 0.01 } },
      boundaries: {
        top: 0, bottom: window.innerHeight,
        left: 0, right: window.innerWidth
      },
      sound: {
        enable: true,
        files: [
          'https://fireworks.js.org/sounds/explosion0.mp3',
          'https://fireworks.js.org/sounds/explosion1.mp3',
          'https://fireworks.js.org/sounds/explosion2.mp3'
        ],
        volume: { min: 4, max: 8 }
      }
    });
  } else {
    console.error("Fireworks.js chưa được load hoặc không có container.");
  }

  function simulateSlot(slot, finalName, names, steps, duration) {
    slot.classList.add("highlight");

    const h = 80;
    const arr = [];
    for (let i = 0; i < steps - 1; i++)
      arr.push(names[Math.floor(Math.random() * names.length)]);
    arr.push(finalName);

    const inner = document.createElement("div");
    inner.className = "slot-inner";
    inner.style.transition = "none";
    inner.style.transform = "translateY(0)";
    slot.innerHTML = "";
    slot.appendChild(inner);

    arr.forEach(n => {
      const d = document.createElement("div");
      d.textContent = n;
      inner.appendChild(d);
    });

    void inner.offsetWidth;

    const totalY = (steps - 1) * h;
    inner.style.transition = `transform ${duration}ms cubic-bezier(0.1,0.57,0.1,1)`;
    inner.style.transform = `translateY(-${totalY}px)`;

    setTimeout(() => {
      slot.classList.remove("highlight");
    }, duration + 200);
  }

  function simulateBoth(t1, t2, names, cb) {
    simulateSlot(slot1, t1, names, 100, 4000);
    simulateSlot(slot2, t2, names, 140, 6000);
    setTimeout(cb, 6300);
  }

  function launchFireworks() {
    if (window.fireworks) {
      fireworks.start();
      setTimeout(() => fireworks.stop(), 8000);
    }
  }

  function showConfetti() {
    confetti({
      particleCount: 400,
      spread: 150,
      origin: { y: 0.6 },
      colors: ['#f1c40f', '#e74c3c', '#2ecc71', '#3498db']
    });
  }

  function showPopup(t1, t2) {
    overlay.style.display = "block";
    popup.innerHTML = `
      <div class="popup-title">TEAM ${index + 1}</div>
      <div class="popup-names">${t1} <span class="dash">–</span> ${t2}</div>
    `;
    popup.style.display = "block";

    launchFireworks();
    showConfetti();

    setTimeout(() => {
      popup.style.display = "none";
      overlay.style.display = "none";
      processing = false;
    }, 4000);
  }

  function showNextTeam() {
    if (processing || index >= teams.length) return;
    processing = true;

    const [t1, t2] = teams[index];
    const names = teams.flatMap(([a, b]) => [a, b]);

    simulateBoth(t1, t2, names, () => {
      showPopup(t1, t2);
      const div = document.createElement("div");
      div.className = "team-item";
      div.textContent = `Team ${index + 1}: ${t1} – ${t2}`;
      teamList.appendChild(div);
      index++;
      if (index >= teams.length)
        document.getElementById("group-form").style.display = "block";
    });
  }

  startBtn.addEventListener("click", showNextTeam);

  window.addEventListener("resize", () => {
    if (window.fireworks)
      fireworks.setOptions({
        boundaries: {
          top: 0, bottom: window.innerHeight,
          left: 0, right: window.innerWidth
        }
      });
  });
});
