(() => {
  "use strict";
  const dialog = document.querySelector(".figure-dialog");
  if (!dialog || typeof dialog.showModal !== "function") return;
  let trigger;
  document.querySelectorAll("[data-figure-open]").forEach((link) => {
    link.addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      trigger = link;
      const image = dialog.querySelector("img");
      image.src = link.href;
      image.alt = link.querySelector("img").alt;
      image.classList.toggle("figure-monochrome", link.classList.contains("figure-plain"));
      const caption = link.closest("figure")?.querySelector("figcaption");
      dialog.querySelector("p").textContent = caption ? caption.textContent : image.alt;
      dialog.showModal();
      document.body.classList.add("figure-is-open");
    });
  });
  dialog.querySelector("button").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  dialog.addEventListener("close", () => {
    document.body.classList.remove("figure-is-open");
    if (trigger) trigger.focus({ preventScroll: true });
  });
})();
