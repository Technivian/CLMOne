/**
 * Canonical workspace tabs: keyboard roving tabindex + responsive More overflow.
 * Expects [data-workspace-tabs] markup from components/_workspace_tabs.html.
 */
(function () {
  function initTabs(root) {
    if (!root || root.dataset.tabsReady === '1') return;
    root.dataset.tabsReady = '1';

    var list = root.querySelector('[data-workspace-tabs-list]');
    var more = root.querySelector('[data-workspace-tabs-more]');
    var morePanel = root.querySelector('[data-workspace-tabs-more-panel]');
    if (!list) return;

    var tabs = Array.prototype.slice.call(list.querySelectorAll('[data-workspace-tab]'));
    var useRoles = root.getAttribute('role') === 'tablist';

    function visibleTabs() {
      return tabs.filter(function (tab) {
        return !tab.hasAttribute('hidden') && tab.offsetParent !== null;
      });
    }

    function focusTab(tab) {
      tabs.forEach(function (item) {
        if (useRoles) item.setAttribute('tabindex', item === tab ? '0' : '-1');
      });
      tab.focus();
    }

    if (useRoles) {
      root.addEventListener('keydown', function (event) {
        var current = event.target.closest('[data-workspace-tab]');
        if (!current || !root.contains(current)) return;
        var items = visibleTabs();
        var index = items.indexOf(current);
        if (index < 0) return;
        var next = null;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
          next = items[(index + 1) % items.length];
        } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
          next = items[(index - 1 + items.length) % items.length];
        } else if (event.key === 'Home') {
          next = items[0];
        } else if (event.key === 'End') {
          next = items[items.length - 1];
        } else {
          return;
        }
        event.preventDefault();
        focusTab(next);
      });
    }

    function syncOverflow() {
      if (!more || !morePanel) return;
      tabs.forEach(function (tab) {
        tab.hidden = false;
        tab.classList.remove('is-overflow');
      });
      more.hidden = true;
      morePanel.innerHTML = '';
      more.removeAttribute('open');

      var overflowAt = Number(root.getAttribute('data-overflow-at') || 0);
      var forceCount = overflowAt > 0;
      var needsOverflow = forceCount
        ? tabs.length > overflowAt
        : list.scrollWidth > list.clientWidth + 1;

      if (!needsOverflow) return;

      var keep = forceCount ? Math.max(1, overflowAt) : Math.max(1, tabs.length - 1);
      if (!forceCount) {
        // Hide from the end until the row fits, keeping the active tab visible when possible.
        keep = tabs.length;
        for (var i = tabs.length - 1; i >= 1; i -= 1) {
          if (list.scrollWidth <= list.clientWidth + 1) break;
          if (tabs[i].classList.contains('is-active')) continue;
          tabs[i].hidden = true;
          tabs[i].classList.add('is-overflow');
          keep = i;
        }
        // If still overflowing, hide inactive earlier tabs too.
        if (list.scrollWidth > list.clientWidth + 1) {
          for (var j = 0; j < tabs.length; j += 1) {
            if (tabs[j].classList.contains('is-active') || tabs[j].hidden) continue;
            tabs[j].hidden = true;
            tabs[j].classList.add('is-overflow');
            if (list.scrollWidth <= list.clientWidth + 1) break;
          }
        }
      } else {
        tabs.forEach(function (tab, index) {
          if (index >= keep && !tab.classList.contains('is-active')) {
            tab.hidden = true;
            tab.classList.add('is-overflow');
          }
        });
      }

      var hidden = tabs.filter(function (tab) { return tab.hidden; });
      if (!hidden.length) return;

      more.hidden = false;
      hidden.forEach(function (tab) {
        var item = document.createElement('a');
        item.href = tab.getAttribute('href') || '#';
        item.className = 'dc-ds-workspace-tabs__more-item' + (tab.classList.contains('is-active') ? ' is-active' : '');
        item.setAttribute('role', 'menuitem');
        item.textContent = tab.textContent.trim();
        morePanel.appendChild(item);
      });
    }

    syncOverflow();
    var resizeTimer = null;
    window.addEventListener('resize', function () {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(syncOverflow, 100);
    });

    document.addEventListener('click', function (event) {
      if (!more || more.hidden) return;
      if (!more.contains(event.target)) more.removeAttribute('open');
    });
  }

  function boot() {
    document.querySelectorAll('[data-workspace-tabs]').forEach(initTabs);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
