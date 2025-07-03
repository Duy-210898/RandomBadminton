document.addEventListener("DOMContentLoaded", () => {
  const boxes = document.querySelectorAll('.table-box');

  let groupIndex = 0;

  function revealNextGroup() {
    if (groupIndex >= boxes.length) return;

    const box = boxes[groupIndex];
    const items = box.querySelectorAll('li');
    let itemIndex = 0;

    function revealNextItem() {
      if (itemIndex >= items.length) {
        groupIndex++;
        setTimeout(revealNextGroup, 800); // chuyển sang bảng kế tiếp sau 0.8s
        return;
      }

      const li = items[itemIndex];
      li.style.opacity = 0;
      li.style.transform = "translateY(-10px)";
      li.classList.add('reveal-match');

      setTimeout(() => {
        li.style.opacity = 1;
        li.style.transform = "translateY(0)";
        li.style.transition = "all 0.5s ease";
        itemIndex++;
        setTimeout(revealNextItem, 300); // delay giữa các trận đấu trong 1 bảng
      }, 50);
    }

    revealNextItem();
  }

  revealNextGroup(); // Bắt đầu khi load
});
