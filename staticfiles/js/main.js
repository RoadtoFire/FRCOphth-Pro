/* ==============================
   MAIN SCRIPT — QUIZ INTERACTIONS
   ============================== */

// Highlight selected option (purely visual, no backend change)
document.addEventListener("DOMContentLoaded", () => {
  const options = document.querySelectorAll(".option-label");

  options.forEach(label => {
    label.addEventListener("click", () => {
      // remove previous
      options.forEach(o => o.classList.remove("selected"));
      label.classList.add("selected");
    });
  });

  // If an explanation exists and you want to toggle manually
  const explanation = document.querySelector(".explanation");
  const feedback = document.querySelector(".feedback");
  if (feedback && explanation) {
    // auto-show explanation after answer
    explanation.classList.add("show");
  }

  // Progress bar animation (if element exists)
  const progressBar = document.querySelector(".progress-bar");
  if (progressBar && progressBar.dataset.width) {
    progressBar.style.width = progressBar.dataset.width + "%";
  }
});

// Optionally: simple smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener("click", function (e) {
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth" });
    }
  });
});


const bar = document.querySelector(".progress-bar");
if (bar && bar.dataset.width) {
  requestAnimationFrame(() => {
    bar.style.width = bar.dataset.width + "%";
  });
}