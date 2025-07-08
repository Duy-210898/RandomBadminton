document.addEventListener("DOMContentLoaded", () => {
  const boxes = document.querySelectorAll('.table-box');

  let groupIndex = 0;

function revealNextGroup() {
  if (groupIndex >= boxes.length) return;

  const box = boxes[groupIndex];
  const groupId = box.dataset.groupId;  // Lấy từ data-group-id
  console.log(`📢 Hiển thị groupId: ${groupId}`);

  const items = box.querySelectorAll('li');
  let itemIndex = 0;

  function revealNextItem() {
    if (itemIndex >= items.length) {
      groupIndex++;
      setTimeout(revealNextGroup, 800);
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
      setTimeout(revealNextItem, 300);
    }, 50);
  }

  revealNextItem();
}

  revealNextGroup(); // Bắt đầu khi load
});
