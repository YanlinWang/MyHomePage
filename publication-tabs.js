(() => {
    const controls = document.querySelector(".publication-tabs");
    const tabs = Array.from(controls.querySelectorAll("a"));
    const panels = tabs.map(tab => document.querySelector(tab.hash));

    controls.setAttribute("role", "tablist");
    tabs.forEach((tab, index) => {
        tab.setAttribute("role", "tab");
        tab.setAttribute("aria-controls", panels[index].id);
        panels[index].setAttribute("role", "tabpanel");
        panels[index].tabIndex = 0;
    });

    function selectTab(activeTab) {
        tabs.forEach((tab, index) => {
            const selected = tab === activeTab;
            tab.setAttribute("aria-selected", String(selected));
            tab.tabIndex = selected ? 0 : -1;
            panels[index].hidden = !selected;
        });
    }

    function activate(tab) {
        selectTab(tab);
        history.replaceState(history.state, "", tab.hash);
    }

    controls.addEventListener("click", event => {
        const tab = event.target.closest("a");
        if (!tab || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        activate(tab);
    });

    controls.addEventListener("keydown", event => {
        const index = tabs.indexOf(event.target);
        if (index < 0) return;
        const destinations = {
            ArrowLeft: tabs[(index + tabs.length - 1) % tabs.length],
            ArrowRight: tabs[(index + 1) % tabs.length],
            Home: tabs[0],
            End: tabs[tabs.length - 1],
            " ": tabs[index],
        };
        const tab = destinations[event.key];
        if (!tab) return;
        event.preventDefault();
        tab.focus();
        activate(tab);
    });

    function revealFragment() {
        const target = document.getElementById(location.hash.slice(1));
        const index = panels.findIndex(panel => panel.contains(target));
        if (index >= 0) {
            selectTab(tabs[index]);
            const archive = target.closest("details");
            if (archive) archive.open = true;
            target.scrollIntoView();
        } else if (!target || target.id === "publications") {
            selectTab(tabs[0]);
        }
    }

    selectTab(tabs[0]);
    revealFragment();
    window.addEventListener("hashchange", revealFragment);
})();
