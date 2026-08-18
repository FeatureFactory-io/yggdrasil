/**
 * VIEW-BROWSE-1 mockup — Views + Filters panel (ESM-06 prototype).
 * One panel: multi-select scope + stereotype-driven field lists.
 * Actions: Clear · Save/Update View · Apply Filters (single primary).
 */
(function () {
  "use strict";

  var STORAGE_KEY = "ygg-mock-browse-views";
  var FIELD_SCHEMA = {};
  var FILTER_CATALOG = { elements: [], relationships: [] };

  function queryFilterControl(idOrTestId) {
    return (
      document.getElementById(idOrTestId) ||
      document.querySelector('[data-testid="' + idOrTestId + '"]')
    );
  }

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
    var schemaEl = document.getElementById("mock-stereotype-field-schema");
    if (schemaEl && schemaEl.textContent) {
      try {
        FIELD_SCHEMA = JSON.parse(schemaEl.textContent);
      } catch (err) {
        console.warn("[mockup:view-browse-1] field schema parse failed", err);
      }
    }
    var catalogEl = document.getElementById("mock-filter-catalog");
    if (catalogEl && catalogEl.textContent) {
      try {
        FILTER_CATALOG = JSON.parse(catalogEl.textContent);
      } catch (err) {
        console.warn("[mockup:view-browse-1] filter catalog parse failed", err);
      }
    }
    return {
      modelSlug: root.dataset.modelSlug || "yggdrasil",
      browseUrl: root.dataset.browseUrl || window.location.pathname,
      maxDepth: parseInt(root.dataset.maxDepth || "5", 10),
      baselineBrowseView: root.dataset.baselineBrowseView || "",
      serverViews: serverViews,
      canSave: root.dataset.canSave !== "false",
    };
  }

  function readMultiSelect(idOrTestId) {
    var el = queryFilterControl(idOrTestId);
    if (!el) return [];
    return Array.prototype.slice
      .call(el.selectedOptions)
      .map(function (opt) {
        return opt.value;
      })
      .filter(Boolean);
  }

  function stereotypeLabel(slug, options) {
    var match = options.find(function (opt) {
      return opt.slug === slug;
    });
    if (match) return match.name;
    return slug.replace(/_/g, " ").replace(/\b\w/g, function (c) {
      return c.toUpperCase();
    });
  }

  function stereotypesForPackages(packages) {
    var scoped = { element: [], relationship: [] };
    if (!FILTER_CATALOG.elements.length) return scoped;

    var pkgSet = {};
    (packages || []).forEach(function (pkg) {
      pkgSet[String(pkg).toLowerCase()] = true;
    });
    var hasPackageFilter = Object.keys(pkgSet).length > 0;

    var elementIds = {};
    var elementStSet = {};
    FILTER_CATALOG.elements.forEach(function (el) {
      if (!hasPackageFilter || pkgSet[el.package]) {
        elementIds[el.id] = true;
        elementStSet[el.stereotype] = true;
      }
    });

    var relStSet = {};
    FILTER_CATALOG.relationships.forEach(function (rel) {
      if (!hasPackageFilter || elementIds[rel.from_id] || elementIds[rel.to_id]) {
        relStSet[rel.edge_stereotype] = true;
      }
    });

    scoped.element = Object.keys(elementStSet).sort();
    scoped.relationship = Object.keys(relStSet).sort();
    return scoped;
  }

  function buildSelectOptions(slugs, selected, allOptions) {
    var selectedSet = {};
    (selected || []).forEach(function (slug) {
      selectedSet[slug] = true;
    });
    return (slugs || [])
      .map(function (slug) {
        var label = stereotypeLabel(slug, allOptions || []);
        var isSelected = !!selectedSet[slug];
        return (
          '<option value="' + slug + '"' + (isSelected ? " selected" : "") + ">" + label + "</option>"
        );
      })
      .join("");
  }

  function repopulateStereotypeSelects() {
    var packages = readMultiSelect("filter-package");
    var scoped = stereotypesForPackages(packages);
    var elementSelect = queryFilterControl("filter-stereotype");
    var relSelect = queryFilterControl("filter-edge-stereotype");
    if (!elementSelect || !relSelect) return;

    var elementSelected = readMultiSelect("filter-stereotype").filter(function (slug) {
      return scoped.element.indexOf(slug) >= 0;
    });
    var relSelected = readMultiSelect("filter-edge-stereotype").filter(function (slug) {
      return scoped.relationship.indexOf(slug) >= 0;
    });

    var elementOptions = scoped.element.map(function (slug) {
      return { slug: slug, name: stereotypeLabel(slug, []) };
    });
    var relOptions = scoped.relationship.map(function (slug) {
      return { slug: slug, name: stereotypeLabel(slug, []) };
    });

    elementSelect.innerHTML = buildSelectOptions(scoped.element, elementSelected, elementOptions);
    relSelect.innerHTML = buildSelectOptions(scoped.relationship, relSelected, relOptions);
    console.log(
      "[mockup:view-browse-1] package scope updated",
      packages,
      scoped
    );
  }

  function readBrowseState() {
    var params = new URLSearchParams(window.location.search);
    return {
      packages: params.getAll("package"),
      element_stereotypes: params.getAll("stereotype"),
      relationship_stereotypes: params.getAll("edge_stereotype"),
      depth: parseInt(params.get("depth") || "2", 10),
      mode: params.get("mode") || params.get("view") || "graph",
      browse_view: params.get("browse_view") || "",
    };
  }

  function readFieldMapFromForm() {
    var map = {};
    document.querySelectorAll(".view-field-section").forEach(function (section) {
      var slug = section.dataset.stereotype;
      if (!slug) return;
      var checked = [];
      section.querySelectorAll(".view-field-checkbox:checked").forEach(function (input) {
        checked.push(input.value);
      });
      if (checked.length) map[slug] = checked;
    });
    return map;
  }

  function readFormState() {
    return {
      packages: readMultiSelect("filter-package") || [],
      element_stereotypes: readMultiSelect("filter-stereotype") || [],
      relationship_stereotypes: readMultiSelect("filter-edge-stereotype") || [],
      depth: parseInt((document.getElementById("depthSlider") || {}).value || "2", 10),
      mode: readBrowseState().mode,
      browse_view: readBrowseState().browse_view,
      field_map: readFieldMapFromForm(),
    };
  }

  function buildQueryString(state, opts) {
    opts = opts || {};
    var params = new URLSearchParams();
    (state.packages || []).forEach(function (v) {
      params.append("package", v);
    });
    (state.element_stereotypes || []).forEach(function (v) {
      params.append("stereotype", v);
    });
    (state.relationship_stereotypes || []).forEach(function (v) {
      params.append("edge_stereotype", v);
    });
    if (state.depth && state.depth !== 2) params.set("depth", String(state.depth));
    if (state.mode && state.mode !== "graph") params.set("mode", state.mode);
    if (opts.browseView) params.set("browse_view", opts.browseView);
    else if (state.browse_view) params.set("browse_view", state.browse_view);
    Object.keys(state.field_map || {}).forEach(function (slug) {
      (state.field_map[slug] || []).forEach(function (path) {
        params.append("field_" + slug, path);
      });
    });
    var qs = params.toString();
    return qs ? "?" + qs : "";
  }

  function payloadFromState(state, opts) {
    opts = opts || {};
    return {
      filters: {
        packages: state.packages || [],
        element_stereotypes: state.element_stereotypes || [],
        relationship_stereotypes: state.relationship_stereotypes || [],
      },
      levels: { depth: state.depth || 2 },
      presentation: state.mode || "graph",
      content: { field_map: state.field_map || {} },
      viewport: opts.includeViewport ? opts.viewport : undefined,
    };
  }

  function navigateToState(state, opts) {
    var url = (opts && opts.browseUrl) || window.location.pathname;
    window.location.href = url + buildQueryString(state, opts);
  }

  function renderFieldSections() {
    var container = document.getElementById("viewFieldSections");
    if (!container) return;
    var existingMap = readFieldMapFromForm();
    var elementSts = readMultiSelect("filter-stereotype");
    var relSts = readMultiSelect("filter-edge-stereotype");
    if (!elementSts.length && !relSts.length) {
      container.innerHTML =
        '<p class="small text-muted mt-2 mb-0" data-testid="view-field-sections-empty">' +
        "Select element or relationship stereotypes to configure visible fields.</p>";
      return;
    }
    var html = "";
    elementSts.forEach(function (slug) {
      html += buildSectionHtml("element", slug, existingMap[slug]);
    });
    relSts.forEach(function (slug) {
      html += buildSectionHtml("relationship", slug, existingMap[slug]);
    });
    container.innerHTML = html;
    bindFieldCheckboxRefresh();
    if (window.mockupRefreshContentLabels) window.mockupRefreshContentLabels();
  }

  function bindFieldCheckboxRefresh() {
    document.querySelectorAll(".view-field-checkbox").forEach(function (input) {
      input.addEventListener("change", function () {
        if (window.mockupRefreshContentLabels) window.mockupRefreshContentLabels();
      });
    });
  }

  function buildSectionHtml(kind, slug, checkedPaths) {
    var fields = FIELD_SCHEMA[slug] || [{ path: "name", label: "Name" }];
    var defaultChecked = fields.map(function (field) {
      return field.path;
    });
    var checkedSet = {};
    (checkedPaths && checkedPaths.length ? checkedPaths : defaultChecked).forEach(function (path) {
      checkedSet[path] = true;
    });
    var label =
      kind === "element"
        ? slug.replace(/_/g, " ").replace(/\b\w/g, function (c) {
            return c.toUpperCase();
          })
        : slug.replace(/_/g, " ");
    var checks = fields
      .map(function (field, idx) {
        var checkedAttr = checkedSet[field.path] ? " checked" : "";
        return (
          '<div class="form-check">' +
          '<input class="form-check-input view-field-checkbox" type="checkbox" ' +
          'name="field_' + slug + '" value="' + field.path + '" ' +
          'id="field-' + slug + "-" + idx + '" ' +
          'data-testid="view-field-' + slug + "-" + field.path + '"' + checkedAttr + ">" +
          '<label class="form-check-label" for="field-' + slug + "-" + idx + '">' + field.label + "</label>" +
          "</div>"
        );
      })
      .join("");
    return (
      '<div class="mt-3 view-field-section" data-stereotype="' + slug + '" data-kind="' + kind + '" ' +
      'data-testid="view-fields-' + slug + '">' +
      '<span class="form-label d-block" style="font-size:0.78rem;font-weight:600;">' +
      label + " — visible fields</span>" +
      '<div class="d-flex flex-wrap gap-3">' + checks + "</div></div>"
    );
  }

  function bindPackageCascade() {
    var pkgSelect = queryFilterControl("filter-package");
    if (!pkgSelect) return;
    pkgSelect.addEventListener("change", function () {
      repopulateStereotypeSelects();
      renderFieldSections();
    });
  }

  function bindStereotypeAutoApply() {
    ["filter-stereotype", "filter-edge-stereotype"].forEach(function (id) {
      var el = queryFilterControl(id);
      if (el) {
        el.addEventListener("change", function () {
          renderFieldSections();
          console.log("[mockup:view-browse-1] stereotype selection changed — field sections updated");
        });
      }
    });
  }

  function storageKey(modelSlug) {
    return STORAGE_KEY + "-" + modelSlug;
  }

  function loadStoredViews(modelSlug) {
    try {
      var raw = sessionStorage.getItem(storageKey(modelSlug));
      return raw ? JSON.parse(raw) : [];
    } catch (err) {
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

  function renderViewsMenu(config) {
    var menu = document.getElementById("viewsDropdownMenu");
    if (!menu) return;
    var stored = loadStoredViews(config.modelSlug);
    var views = mergeViews(config.serverViews, stored);
    menu.innerHTML = "";
    if (!views.length) {
      menu.innerHTML = '<li><span class="dropdown-item-text text-muted small">No saved views yet</span></li>';
    } else {
      views.forEach(function (view) {
        var li = document.createElement("li");
        li.className = "d-flex align-items-center gap-1 px-2";
        var link = document.createElement("a");
        link.className = "dropdown-item flex-grow-1";
        link.href = config.browseUrl + "?browse_view=" + encodeURIComponent(view.slug);
        link.setAttribute("data-testid", "view-option-" + view.slug);
        link.textContent = view.name;
        li.appendChild(link);
        if (view.deletable && config.canSave) {
          var del = document.createElement("button");
          del.type = "button";
          del.className = "btn btn-sm btn-link text-danger p-0";
          del.setAttribute("data-testid", "delete-view-btn");
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

  function captureViewport() {
    var cy = window.cyInstance;
    if (!cy) return null;
    return {
      zoom: cy.zoom(),
      pan: cy.pan(),
      center_element_id: window.selectedElementId ? String(window.selectedElementId) : null,
    };
  }

  function saveCurrentView(config) {
    var nameInput = document.getElementById("saveViewNameInput");
    var name = (nameInput && nameInput.value.trim()) || "";
    if (!name) {
      nameInput && nameInput.focus();
      return;
    }
    var state = readFormState();
    var includeViewport =
      document.getElementById("saveViewIncludeViewport") &&
      document.getElementById("saveViewIncludeViewport").checked;
    var payload = payloadFromState(state, {
      includeViewport: includeViewport,
      viewport: includeViewport ? captureViewport() : null,
    });
    if (!includeViewport) delete payload.viewport;
    var slug = slugify(name);
    var stored = loadStoredViews(config.modelSlug);
    var entry = { name: name, slug: slug, model_slug: config.modelSlug, payload: payload };
    var idx = stored.findIndex(function (v) {
      return v.slug === slug;
    });
    if (idx >= 0) stored[idx] = entry;
    else stored.push(entry);
    saveStoredViews(config.modelSlug, stored);
    renderViewsMenu(config);
    showToast('View "' + name + '" saved.');
    var modal = document.getElementById("saveViewModal");
    if (modal && window.bootstrap) bootstrap.Modal.getInstance(modal)?.hide();
    if (nameInput) nameInput.value = "";
  }

  function deleteView(config, slug) {
    var stored = loadStoredViews(config.modelSlug);
    saveStoredViews(
      config.modelSlug,
      stored.filter(function (v) {
        return v.slug !== slug;
      })
    );
    renderViewsMenu(config);
    showToast("View removed.");
  }

  function bindSaveModal(config) {
    var confirm = document.getElementById("saveViewConfirmBtn");
    if (confirm) confirm.addEventListener("click", function () { saveCurrentView(config); });
  }

  function bindFilterForm(config) {
    var form = document.getElementById("filterForm");
    if (!form) return;
    form.addEventListener("submit", function (evt) {
      evt.preventDefault();
      var state = readFormState();
      state.browse_view = "";
      console.log("[mockup:view-browse-1] apply filters", state);
      navigateToState(state, { browseUrl: config.browseUrl });
    });
  }

  function bindClearView(config) {
    var btn = document.getElementById("clearViewBtn");
    if (!btn) return;
    btn.addEventListener("click", function (evt) {
      evt.preventDefault();
      if (config.baselineBrowseView) {
        window.location.href =
          config.browseUrl + "?browse_view=" + encodeURIComponent(config.baselineBrowseView);
        return;
      }
      var state = readBrowseState();
      navigateToState(
        {
          packages: [],
          element_stereotypes: [],
          relationship_stereotypes: [],
          depth: state.depth,
          mode: state.mode,
          browse_view: "",
          field_map: {},
        },
        { browseUrl: config.browseUrl }
      );
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
      navigateToState(Object.assign(readFormState(), { depth: state.depth }), { browseUrl: config.browseUrl });
    });
  }

  function bindModeToggle(config) {
    window.mockupSetView = function (mode) {
      var state = readFormState();
      state.mode = mode;
      navigateToState(state, { browseUrl: config.browseUrl });
    };
  }

  function initViewBrowser() {
    var config = readConfig();
    if (!config) return;
    window.mockupReadFormState = readFormState;
    renderViewsMenu(config);
    bindSaveModal(config);
    bindFilterForm(config);
    bindClearView(config);
    bindDepthSlider(config);
    bindModeToggle(config);
    bindPackageCascade();
    bindStereotypeAutoApply();
    bindFieldCheckboxRefresh();
    console.log("[mockup:view-browse-1] Filters-first View ready | model=" + config.modelSlug);
  }

  document.addEventListener("DOMContentLoaded", initViewBrowser);
})();
