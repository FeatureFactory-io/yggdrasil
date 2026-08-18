/**
 * VIEW-BROWSE-1 mockup — Views v1 client simulation (ESM-06).
 * Dual persistence: live URL query string + sessionStorage named Views.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "ygg-mock-browse-views";

  function readConfig() {
    var root = document.getElementById("browserRoot");
    if (!root) return null;
    var serverEl = document.getElementById("mock-server-views");
    var serverViews = [];
    if (serverEl && serverEl.textContent) {
      try {
        serverViews = JSON.parse(serverEl.textContent);
      } catch (err) {
        console.warn("[mockup:view-browse-1] server views parse failed", err);
      }
    }
    return {
      modelSlug: root.dataset.modelSlug || "yggdrasil",
      browseUrl: root.dataset.browseUrl || window.location.pathname,
      maxDepth: parseInt(root.dataset.maxDepth || "5", 10),
      serverViews: serverViews,
      canSave: root.dataset.canSave !== "false",
    };
  }

  function storageKey(modelSlug) {
    return STORAGE_KEY + "-" + modelSlug;
  }

  function loadStoredViews(modelSlug) {
    try {
      var raw = sessionStorage.getItem(storageKey(modelSlug));
      return raw ? JSON.parse(raw) : [];
    } catch (err) {
      console.warn("[mockup:view-browse-1] sessionStorage read failed", err);
      return [];
    }
  }

  function saveStoredViews(modelSlug, views) {
    sessionStorage.setItem(storageKey(modelSlug), JSON.stringify(views));
  }

  function mergeViews(serverViews, storedViews) {
    var bySlug = {};
    serverViews.forEach(function (v) {
      bySlug[v.slug] = Object.assign({ deletable: false, source: "server" }, v);
    });
    storedViews.forEach(function (v) {
      bySlug[v.slug] = Object.assign({ deletable: true, source: "session" }, v);
    });
    return Object.keys(bySlug)
      .map(function (slug) {
        return bySlug[slug];
      })
      .sort(function (a, b) {
        return a.name.localeCompare(b.name);
      });
  }

  function slugify(name) {
    return name
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .trim()
      .replace(/[\s_]+/g, "-")
      .slice(0, 64) || "view";
  }

  function readBrowseState() {
    var params = new URLSearchParams(window.location.search);
    return {
      package: params.get("package") || "",
      stereotype: params.get("stereotype") || "",
      health: params.get("health") || "",
      as_of: params.get("as_of") || "",
      depth: parseInt(params.get("depth") || "2", 10),
      mode: params.get("mode") || params.get("view") || "graph",
      browse_view: params.get("browse_view") || "",
    };
  }

  function readFormState() {
    return {
      package: (document.querySelector('[data-testid="filter-package"]') || {}).value || "",
      stereotype: (document.querySelector('[data-testid="filter-stereotype"]') || {}).value || "",
      health: (document.querySelector('[data-testid="filter-health"]') || {}).value || "",
      as_of: (document.querySelector('[data-testid="filter-as-of"]') || {}).value || "",
      depth: parseInt(
        (document.getElementById("depthSlider") || {}).value || "2",
        10
      ),
      mode: readBrowseState().mode,
      browse_view: "",
    };
  }

  function buildQueryString(state, opts) {
    opts = opts || {};
    var params = new URLSearchParams();
    if (state.package) params.set("package", state.package);
    if (state.stereotype) params.set("stereotype", state.stereotype);
    if (state.health) params.set("health", state.health);
    if (state.as_of) params.set("as_of", state.as_of);
    if (state.depth && state.depth !== 2) params.set("depth", String(state.depth));
    if (state.mode && state.mode !== "graph") params.set("mode", state.mode);
    if (opts.browseView) params.set("browse_view", opts.browseView);
    var qs = params.toString();
    return qs ? "?" + qs : "";
  }

  function payloadFromState(state) {
    return {
      filters: {
        package: state.package || null,
        stereotype: state.stereotype || null,
        health: state.health || null,
        as_of: state.as_of || null,
        rules: null,
      },
      levels: { depth: state.depth || 2 },
      presentation: state.mode || "graph",
    };
  }

  function navigateToState(state, opts) {
    var url = (opts && opts.browseUrl) || window.location.pathname;
    window.location.href = url + buildQueryString(state, opts);
  }

  function renderViewsMenu(config) {
    var menu = document.getElementById("viewsDropdownMenu");
    if (!menu) return;

    var stored = loadStoredViews(config.modelSlug);
    var views = mergeViews(config.serverViews, stored);
    menu.innerHTML = "";

    if (!views.length) {
      var empty = document.createElement("li");
      empty.innerHTML =
        '<span class="dropdown-item-text text-muted small">No saved views yet</span>';
      menu.appendChild(empty);
    } else {
      views.forEach(function (view) {
        var li = document.createElement("li");
        li.className = "d-flex align-items-center gap-1 px-2";
        var link = document.createElement("a");
        link.className = "dropdown-item flex-grow-1";
        link.href =
          config.browseUrl + "?browse_view=" + encodeURIComponent(view.slug);
        link.setAttribute("data-testid", "view-option-" + view.slug);
        link.textContent = view.name;
        link.addEventListener("click", function () {
          console.log(
            "[mockup:view-browse-1] load view slug=" + view.slug + " source=" + view.source
          );
        });
        li.appendChild(link);
        if (view.deletable && config.canSave) {
          var del = document.createElement("button");
          del.type = "button";
          del.className = "btn btn-sm btn-link text-danger p-0";
          del.setAttribute("data-testid", "delete-view-btn");
          del.setAttribute("aria-label", "Delete view " + view.name);
          del.innerHTML = '<i class="fa-solid fa-trash-can" aria-hidden="true"></i>';
          del.addEventListener("click", function (evt) {
            evt.preventDefault();
            evt.stopPropagation();
            deleteView(config, view.slug);
          });
          li.appendChild(del);
        }
        menu.appendChild(li);
      });
    }

    var divider = document.createElement("li");
    divider.innerHTML = '<hr class="dropdown-divider">';
    menu.appendChild(divider);

    if (config.canSave) {
      var saveLi = document.createElement("li");
      var saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.className = "dropdown-item";
      saveBtn.setAttribute("data-testid", "save-view-btn");
      saveBtn.setAttribute("data-bs-toggle", "modal");
      saveBtn.setAttribute("data-bs-target", "#saveViewModal");
      saveBtn.textContent = "Save current view…";
      saveLi.appendChild(saveBtn);
      menu.appendChild(saveLi);
    }
  }

  function showToast(message) {
    var toastEl = document.getElementById("viewSaveToast");
    if (!toastEl || !window.bootstrap) {
      console.log("[mockup:view-browse-1] toast: " + message);
      return;
    }
    toastEl.querySelector(".toast-body").textContent = message;
    bootstrap.Toast.getOrCreateInstance(toastEl).show();
  }

  function saveCurrentView(config) {
    var nameInput = document.getElementById("saveViewNameInput");
    var name = (nameInput && nameInput.value.trim()) || "";
    if (!name) {
      nameInput && nameInput.focus();
      return;
    }
    var state = readFormState();
    var slug = slugify(name);
    var stored = loadStoredViews(config.modelSlug);
    var entry = {
      name: name,
      slug: slug,
      model_slug: config.modelSlug,
      payload: payloadFromState(state),
    };
    var idx = stored.findIndex(function (v) {
      return v.slug === slug;
    });
    if (idx >= 0) stored[idx] = entry;
    else stored.push(entry);
    saveStoredViews(config.modelSlug, stored);
    console.log("[mockup:view-browse-1] saved view slug=" + slug, entry.payload);
    renderViewsMenu(config);
    showToast('View "' + name + '" saved.');
    var modal = document.getElementById("saveViewModal");
    if (modal && window.bootstrap) {
      bootstrap.Modal.getInstance(modal)?.hide();
    }
    if (nameInput) nameInput.value = "";
  }

  function deleteView(config, slug) {
    var stored = loadStoredViews(config.modelSlug);
    var next = stored.filter(function (v) {
      return v.slug !== slug;
    });
    saveStoredViews(config.modelSlug, next);
    console.log("[mockup:view-browse-1] deleted view slug=" + slug);
    renderViewsMenu(config);
    showToast("View removed.");
  }

  function bindSaveModal(config) {
    var confirm = document.getElementById("saveViewConfirmBtn");
    if (confirm) {
      confirm.addEventListener("click", function () {
        saveCurrentView(config);
      });
    }
  }

  function bindFilterForm(config) {
    var form = document.getElementById("filterForm");
    if (!form) return;
    form.addEventListener("submit", function (evt) {
      evt.preventDefault();
      var state = readFormState();
      state.mode = readBrowseState().mode;
      console.log("[mockup:view-browse-1] apply filters", state);
      navigateToState(state, { browseUrl: config.browseUrl });
    });
  }

  function bindClearFilters(config) {
    document.querySelectorAll('[data-action="clear-filters"]').forEach(function (btn) {
      btn.addEventListener("click", function (evt) {
        evt.preventDefault();
        var state = readBrowseState();
        console.log("[mockup:view-browse-1] clear filters (views catalog unchanged)");
        navigateToState(
          { package: "", stereotype: "", health: "", as_of: "", depth: state.depth, mode: state.mode },
          { browseUrl: config.browseUrl }
        );
      });
    });
  }

  function bindDepthSlider(config) {
    var slider = document.getElementById("depthSlider");
    if (!slider) return;
    slider.addEventListener("change", function () {
      var state = readBrowseState();
      state.depth = parseInt(slider.value, 10);
      var badge = document.querySelector('[data-testid="browser-depth-value"]');
      if (badge) badge.textContent = state.depth + " / " + config.maxDepth;
      console.log("[mockup:view-browse-1] depth changed to " + state.depth);
      navigateToState(state, { browseUrl: config.browseUrl });
    });
  }

  function bindModeToggle(config) {
    window.mockupSetView = function (mode) {
      var state = readBrowseState();
      state.mode = mode;
      console.log("[mockup:view-browse-1] mode toggled to " + mode);
      navigateToState(state, { browseUrl: config.browseUrl });
    };
  }

  function initViewsV1() {
    var config = readConfig();
    if (!config) return;
    renderViewsMenu(config);
    bindSaveModal(config);
    bindFilterForm(config);
    bindClearFilters(config);
    bindDepthSlider(config);
    bindModeToggle(config);
    console.log(
      "[mockup:view-browse-1] Views v1 ready | model=" +
        config.modelSlug +
        " server_views=" +
        config.serverViews.length
    );
  }

  document.addEventListener("DOMContentLoaded", initViewsV1);
})();
