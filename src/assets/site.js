(() => {
  const tabs = [...document.querySelectorAll(".tour-tab")];
  const panels = tabs.map(tab => document.getElementById(tab.hash.slice(1)));
  if (tabs.length && panels.every(Boolean)) {
    const tabList = tabs[0].parentElement;
    tabList.setAttribute("role", "tablist");
    panels[0].parentElement.classList.add("has-tabs");

    const select = (index, focus) => {
      tabs.forEach((tab, i) => {
        tab.setAttribute("aria-selected", String(i === index));
        tab.tabIndex = i === index ? 0 : -1;
        panels[i].hidden = i !== index;
      });
      if (focus) tabs[index].focus();
    };

    tabs.forEach((tab, i) => {
      tab.setAttribute("role", "tab");
      tab.setAttribute("aria-controls", panels[i].id);
      panels[i].setAttribute("role", "tabpanel");
      panels[i].setAttribute("aria-labelledby", tab.id);
      tab.addEventListener("click", event => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        select(i, false);
      });
      tab.addEventListener("keydown", event => {
        const next = {
          ArrowRight: (i + 1) % tabs.length,
          ArrowLeft: (i + tabs.length - 1) % tabs.length,
          Home: 0,
          End: tabs.length - 1
        }[event.key];
        if (next !== undefined) {
          event.preventDefault();
          select(next, true);
        }
      });
    });
    const indexForHash = () => tabs.findIndex(tab => tab.hash === location.hash);
    select(Math.max(0, indexForHash()), false);
    window.addEventListener("hashchange", () => {
      const index = indexForHash();
      if (index >= 0) select(index, false);
    });
  }

  const dialog = document.querySelector(".screen-dialog");
  if (dialog && typeof dialog.showModal === "function") {
    const title = dialog.querySelector("#screen-dialog-title");
    const image = dialog.querySelector("img");
    document.querySelectorAll(".screen-link").forEach(link => {
      link.addEventListener("click", event => {
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        image.src = link.href;
        image.alt = link.querySelector("img").alt;
        title.textContent = link.dataset.screenTitle;
        dialog.showModal();
        dialog.scrollTop = 0;
      });
    });
    dialog.addEventListener("click", event => {
      if (event.target !== dialog) return;
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right ||
          event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    });
  }

  const menu = document.querySelector(".mobile-menu");
  if (menu) {
    menu.querySelectorAll("a").forEach(link => link.addEventListener("click", () => { menu.open = false; }));
    window.addEventListener("click", event => {
      if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
    menu.addEventListener("keydown", event => {
      if (event.key === "Escape" && menu.open) {
        menu.open = false;
        menu.querySelector("summary").focus();
      }
    });
  }
})();
