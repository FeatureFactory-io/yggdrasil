/**
 * Diagram mockups — ESM-06 functional prototype (client-side play-pretend).
 * DIAGRAM-LIST+FIND-1 · DIAGRAM-EDITOR-1 · DIAGRAM-CREATE/DELETE/MOVE
 */
(function () {
  "use strict";

  var STORAGE_KEY = "ygg-mock-diagrams";
  var LOG = "[mockup:diagram]";

  function log(event, detail) {
    if (detail !== undefined) {
      console.log(LOG + " " + event, detail);
    } else {
      console.log(LOG + " " + event);
    }
  }

  function parseJson(elId, fallback) {
    var el = document.getElementById(elId);
    if (!el || !el.textContent) return fallback;
    try {
      return JSON.parse(el.textContent);
    } catch (err) {
      console.warn(LOG + " parse failed:" + elId, err);
      return fallback;
    }
  }

  function loadState() {
    try {
      var raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    } catch (err) {
      console.warn(LOG + " storage read failed", err);
    }
    return null;
  }

  function saveState(state) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function defaultPresentation(nodes, edges) {
    return {
      nodes: nodes || [],
      edges: edges || [],
    };
  }

  function seedState(seed) {
    var diagrams = (seed.diagrams || []).map(function (d) {
      return Object.assign({}, d, { has_draft: !!d.has_draft });
    });
    var presentations = seed.presentations || {};
    var drafts = {};
    diagrams.forEach(function (d) {
      if (d.has_draft && presentations[String(d.id)]) {
        drafts[String(d.id)] = {
          presentation: JSON.parse(JSON.stringify(presentations[String(d.id)])),
          dirty: true,
        };
      }
    });
    return {
      diagrams: diagrams,
      presentations: presentations,
      drafts: drafts,
      nextId: seed.nextId || 100,
      createSessions: {},
    };
  }

  function getStore(seed) {
    var state = loadState();
    if (!state) {
      state = seedState(seed || { diagrams: [], presentations: {} });
      saveState(state);
      log("store seeded", { count: state.diagrams.length });
    }
    return state;
  }

  function persist(state) {
    saveState(state);
  }

  function diagramById(state, id) {
    var sid = String(id);
    return state.diagrams.find(function (d) {
      return String(d.id) === sid;
    });
  }

  function listGrouped(state, filter) {
    var q = (filter && filter.query ? filter.query : "").toLowerCase();
    var pkg = filter && filter.package ? filter.package : "";
    var rows = state.diagrams.filter(function (d) {
      if (pkg && pkg !== "All packages" && d.package !== pkg) return false;
      if (!q) return true;
      var hay = (d.name + " " + d.summary + " " + d.tags.join(" ")).toLowerCase();
      return hay.indexOf(q) >= 0;
    });
    var groups = {};
    rows.forEach(function (d) {
      var hasDraft = !!state.drafts[String(d.id)];
      var enriched = Object.assign({}, d, { has_draft: hasDraft });
      if (!groups[d.package]) groups[d.package] = [];
      groups[d.package].push(enriched);
    });
    return Object.keys(groups)
      .sort()
      .map(function (packageName) {
        return { package: packageName, diagrams: groups[packageName] };
      });
  }

  function getPresentation(state, diagramId) {
    var sid = String(diagramId);
    if (state.drafts[sid]) return state.drafts[sid].presentation;
    if (state.presentations[sid]) return state.presentations[sid];
    return defaultPresentation([], []);
  }

  function setDraft(state, diagramId, presentation) {
    state.drafts[String(diagramId)] = { presentation: presentation, dirty: true };
    persist(state);
    log("draft updated", { diagramId: diagramId });
  }

  function clearDraft(state, diagramId) {
    delete state.drafts[String(diagramId)];
    persist(state);
    log("draft cleared", { diagramId: diagramId });
  }

  function deleteDiagram(state, diagramId) {
    var sid = String(diagramId);
    state.diagrams = state.diagrams.filter(function (d) {
      return String(d.id) !== sid;
    });
    delete state.presentations[sid];
    delete state.drafts[sid];
    persist(state);
    log("diagram deleted", { diagramId: diagramId });
  }

  function moveDiagram(state, diagramId, targetPackage) {
    var d = diagramById(state, diagramId);
    if (!d) return;
    d.package = targetPackage;
    persist(state);
    log("diagram moved", { diagramId: diagramId, package: targetPackage });
  }

  function muninSummary(name, nodeLabels) {
    var joined = nodeLabels.slice(0, 4).join(", ");
    var suffix = nodeLabels.length > 4 ? "…" : "";
    return name + " — " + (joined || "empty canvas") + suffix;
  }

  function muninTags(nodeLabels) {
    return nodeLabels
      .slice(0, 5)
      .map(function (label) {
        return label.toLowerCase().replace(/\s+/g, "-");
      })
      .filter(Boolean);
  }

  function commitDiagram(state, diagramId, presentation, meta) {
    var sid = String(diagramId);
    var d = diagramById(state, sid);
    if (!d) return null;
    var labels = (presentation.nodes || []).map(function (n) {
      return n.label;
    });
    d.summary = muninSummary(d.name, labels);
    d.tags = muninTags(labels);
    if (meta) {
      if (meta.name) d.name = meta.name;
      if (meta.package) d.package = meta.package;
      if (meta.kind) d.kind = meta.kind;
    }
    state.presentations[sid] = JSON.parse(JSON.stringify(presentation));
    delete state.drafts[sid];
    persist(state);
    log("diagram saved (Munin pretend)", { diagramId: sid, summary: d.summary });
    return d;
  }

  function createDiagram(state, fields) {
    var id = state.nextId;
    state.nextId += 1;
    var diagram = {
      id: id,
      name: fields.name,
      kind: fields.kind,
      package: fields.package,
      summary: "New diagram — not yet saved",
      tags: [],
      has_draft: true,
    };
    state.diagrams.push(diagram);
    state.drafts[String(id)] = {
      presentation: defaultPresentation([], []),
      dirty: true,
    };
    persist(state);
    log("diagram created", { id: id, name: fields.name });
    return diagram;
  }

  function createSession(state, fields) {
    var sessionId = "session-" + Date.now();
    state.createSessions[sessionId] = {
      name: fields.name,
      package: fields.package,
      kind: fields.kind,
      presentation: defaultPresentation([], []),
      dirty: false,
    };
    persist(state);
    log("create session opened", { sessionId: sessionId });
    return sessionId;
  }

  function getCreateSession(state, sessionId) {
    return state.createSessions[sessionId] || null;
  }

  function updateCreateSession(state, sessionId, presentation) {
    var session = state.createSessions[sessionId];
    if (!session) return;
    session.presentation = presentation;
    session.dirty = true;
    persist(state);
  }

  function commitCreateSession(state, sessionId) {
    var session = state.createSessions[sessionId];
    if (!session) return null;
    var diagram = createDiagram(state, {
      name: session.name,
      package: session.package,
      kind: session.kind,
    });
    commitDiagram(state, diagram.id, session.presentation);
    delete state.createSessions[sessionId];
    persist(state);
    return diagram;
  }

  function discardCreateSession(state, sessionId) {
    delete state.createSessions[sessionId];
    persist(state);
    log("create session discarded", { sessionId: sessionId });
  }

  function showToast(message, variant) {
    var container = document.querySelector(".toast-container");
    if (!container || !window.bootstrap) {
      log("toast", message);
      return;
    }
    var el = document.createElement("div");
    el.className =
      "toast align-items-center text-bg-" + (variant || "success") + " border-0 show";
    el.setAttribute("role", "status");
    el.innerHTML =
      '<div class="d-flex"><div class="toast-body"></div>' +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
    el.querySelector(".toast-body").textContent = message;
    container.appendChild(el);
    var toast = bootstrap.Toast.getOrCreateInstance(el, { delay: 3200 });
    toast.show();
    el.addEventListener("hidden.bs.toast", function () {
      el.remove();
    });
  }

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  /* ── LIST PAGE ─────────────────────────────────────────────────── */

  function initListPage() {
    var root = document.querySelector('[data-testid="diagram-list-page"]');
    if (!root) return;

    var seed = parseJson("mock-diagram-seed", { diagrams: [], presentations: {} });
    var config = parseJson("mock-diagram-config", { urls: {} });
    var state = getStore(seed);
    var mount = document.getElementById("diagram-list-mount");
    var searchInput = root.querySelector('[aria-label="Search diagrams"]');
    var pkgFilter = root.querySelector('[data-testid="diagram-filter-package"]');
    var pendingDeleteId = null;
    var pendingMoveId = null;

    function editorUrl(id) {
      var tpl = config.urls.editor || "/mockups/diagram/{id}/edit/";
      return tpl.replace("{id}", String(id));
    }

    function render() {
      var groups = listGrouped(state, {
        query: searchInput ? searchInput.value : "",
        package: pkgFilter ? pkgFilter.value : "",
      });
      if (!mount) return;
      if (!groups.length) {
        mount.innerHTML =
          '<div class="text-center py-5" data-testid="diagram-empty-state">' +
          '<i class="fa-solid fa-sitemap fa-2x mb-3 d-block" style="color:var(--hg-border);" aria-hidden="true"></i>' +
          '<p class="mb-1 fw-medium text-muted">No diagrams match.</p>' +
          '<p class="small mb-3 text-muted">Try clearing filters or create a diagram from View Browser or here.</p>' +
          '<a href="' +
          escapeHtml(config.urls.create || "/mockups/diagram/create/") +
          '" class="btn btn-primary btn-sm" data-testid="diagram-empty-create-btn">' +
          '<i class="fa-solid fa-plus me-1" aria-hidden="true"></i>Create Diagram</a></div>';
        return;
      }
      var html =
        '<table class="table table-hover align-middle mb-0" data-testid="diagram-table" aria-label="Diagrams table">' +
        '<thead class="table-light"><tr>' +
        "<th>Name</th><th>Kind</th><th>Package</th><th>Summary</th><th>Tags</th>" +
        '<th class="text-end">Actions</th></tr></thead><tbody>';
      groups.forEach(function (group) {
        html +=
          '<tr class="table-light"><td colspan="6" class="py-1">' +
          '<span class="hg-section-label text-uppercase">' +
          escapeHtml(group.package) +
          "</span></td></tr>";
        group.diagrams.forEach(function (d) {
          html += '<tr data-testid="diagram-row-' + d.id + '"><td>';
          html +=
            '<span class="st-icon st-icon-diagram me-1" aria-hidden="true"><i class="fa-solid fa-sitemap"></i></span>';
          html +=
            '<a href="' +
            editorUrl(d.id) +
            '" class="fw-semibold text-decoration-none">' +
            escapeHtml(d.name) +
            "</a>";
          if (d.has_draft) {
            html +=
              ' <span class="badge bg-warning text-dark ms-1" data-testid="diagram-draft-badge">Draft</span>';
          }
          html += "</td><td>";
          html +=
            '<span class="badge" style="background:var(--hg-primary-100);color:var(--hg-primary);font-size:0.7rem;">' +
            escapeHtml(d.kind) +
            "</span></td>";
          html += '<td class="text-muted">' + escapeHtml(d.package) + "</td>";
          html += '<td class="text-muted small">' + escapeHtml(d.summary) + "</td><td class=\"text-muted small\">";
          (d.tags || []).forEach(function (tag) {
            html +=
              '<span class="badge bg-secondary-subtle text-secondary me-1">' + escapeHtml(tag) + "</span>";
          });
          html += '</td><td class="text-end"><div class="btn-group btn-group-sm" role="group">';
          html +=
            '<a href="' +
            editorUrl(d.id) +
            '" class="btn btn-outline-secondary" data-bs-toggle="tooltip" title="Edit diagram layout" aria-label="Edit ' +
            escapeHtml(d.name) +
            '" data-testid="diagram-edit-' +
            d.id +
            '"><i class="fa-solid fa-pen" aria-hidden="true"></i></a>';
          html +=
            '<button type="button" class="btn btn-outline-secondary" data-bs-toggle="tooltip" title="Move to another package" aria-label="Move ' +
            escapeHtml(d.name) +
            '" data-testid="diagram-move-' +
            d.id +
            '" data-diagram-id="' +
            d.id +
            '"><i class="fa-solid fa-folder-tree" aria-hidden="true"></i></button>';
          html +=
            '<button type="button" class="btn btn-outline-danger" data-bs-toggle="tooltip" title="Delete diagram view" aria-label="Delete ' +
            escapeHtml(d.name) +
            '" data-testid="diagram-delete-' +
            d.id +
            '" data-diagram-id="' +
            d.id +
            '"><i class="fa-solid fa-trash" aria-hidden="true"></i></button></div></td></tr>';
        });
      });
      html += "</tbody></table>";
      mount.innerHTML = html;
      bindRowActions();
      if (window.bootstrap && bootstrap.Tooltip) {
        mount.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
          bootstrap.Tooltip.getOrCreateInstance(el);
        });
      }
    }

    function bindRowActions() {
      mount.querySelectorAll("[data-diagram-id]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var id = btn.getAttribute("data-diagram-id");
          var d = diagramById(state, id);
          if (!d) return;
          if (btn.getAttribute("data-testid").indexOf("delete") >= 0) {
            pendingDeleteId = id;
            document.getElementById("deleteDiagramName").textContent = d.name;
            bootstrap.Modal.getOrCreateInstance(document.getElementById("diagramDeleteModal")).show();
          } else {
            pendingMoveId = id;
            document.getElementById("moveDiagramName").textContent = d.name;
            document.getElementById("moveCurrentPackage").value = d.package;
            bootstrap.Modal.getOrCreateInstance(document.getElementById("diagramMoveModal")).show();
          }
        });
      });
    }

    document.querySelector('[data-testid="diagram-confirm-delete-btn"]').addEventListener("click", function () {
      if (!pendingDeleteId) return;
      deleteDiagram(state, pendingDeleteId);
      pendingDeleteId = null;
      bootstrap.Modal.getInstance(document.getElementById("diagramDeleteModal")).hide();
      render();
      showToast("Diagram deleted (mock Munin ChangeSet)", "success");
    });

    document.querySelector('[data-testid="diagram-confirm-move-btn"]').addEventListener("click", function () {
      if (!pendingMoveId) return;
      var target = document.getElementById("moveTargetPackage").value;
      moveDiagram(state, pendingMoveId, target);
      pendingMoveId = null;
      bootstrap.Modal.getInstance(document.getElementById("diagramMoveModal")).hide();
      render();
      showToast("Diagram moved to " + target, "success");
    });

    if (searchInput) searchInput.addEventListener("input", render);
    if (pkgFilter) pkgFilter.addEventListener("change", render);

    var params = new URLSearchParams(window.location.search);
    if (params.get("saved") === "1") showToast("Diagram saved — Munin enriched summary & tags", "success");
    if (params.get("discarded") === "1") showToast("Draft discarded", "secondary");

    render();
    log("list page ready");
  }

  /* ── EDITOR PAGE ───────────────────────────────────────────────── */

  function presentationFromCy(cy) {
    var nodes = cy.nodes().map(function (n) {
      var p = n.position();
      return { id: n.id(), label: n.data("label"), x: p.x, y: p.y };
    });
    var edges = cy.edges().map(function (e) {
      return {
        id: e.id(),
        source: e.source().id(),
        target: e.target().id(),
        label: e.data("label") || "depends_on",
      };
    });
    return { nodes: nodes, edges: edges };
  }

  function cyElementsFromPresentation(presentation) {
    var nodes = (presentation.nodes || []).map(function (n) {
      return {
        data: { id: String(n.id), label: n.label },
        position: { x: n.x || 100, y: n.y || 100 },
      };
    });
    var edges = (presentation.edges || []).map(function (e) {
      return {
        data: {
          id: String(e.id),
          source: String(e.source),
          target: String(e.target),
          label: e.label || "depends_on",
        },
      };
    });
    return { nodes: nodes, edges: edges };
  }

  function initEditorPage() {
    var root = document.querySelector('[data-testid="diagram-editor-page"]');
    if (!root) return;

    var seed = parseJson("mock-diagram-seed", { diagrams: [], presentations: {} });
    var config = parseJson("mock-diagram-editor-config", {});
    var state = getStore(seed);
    var mode = config.mode || "edit";
    var diagramId = config.diagramId;
    var sessionId = config.sessionId;
    var cy = null;
    var drawMode = false;
    var drawSource = null;
    var selectedEdgeStereotype = "depends_on";
    var nextNodeId = 900;

    var draftBadge = root.querySelector('[data-testid="diagram-draft-badge"]');
    var titleEl = root.querySelector(".yrg-diagram-header h1");
    var metaEl = root.querySelector(".yrg-diagram-header .small.text-muted");

    function listUrl(query) {
      var base = config.urls.list || "/mockups/diagram/";
      return query ? base + "?" + query : base;
    }

    function setDraftVisible(visible) {
      if (!draftBadge) {
        if (visible) {
          var h1 = root.querySelector(".yrg-diagram-header h1");
          if (h1 && !root.querySelector('[data-testid="diagram-draft-badge"]')) {
            var badge = document.createElement("span");
            badge.className = "badge bg-warning text-dark ms-2";
            badge.setAttribute("data-testid", "diagram-draft-badge");
            badge.textContent = "Draft";
            h1.insertAdjacentElement("afterend", badge);
            draftBadge = badge;
          }
        }
        return;
      }
      draftBadge.classList.toggle("d-none", !visible);
    }

    function markDirty() {
      setDraftVisible(true);
      var pres = presentationFromCy(cy);
      if (mode === "create" && sessionId) {
        updateCreateSession(state, sessionId, pres);
      } else if (diagramId) {
        setDraft(state, diagramId, pres);
      }
    }

    function loadPresentation() {
      if (mode === "create" && sessionId) {
        var session = getCreateSession(state, sessionId);
        if (!session) return defaultPresentation([], []);
        if (titleEl) titleEl.textContent = session.name;
        if (metaEl) metaEl.textContent = session.package + " · " + session.kind;
        setDraftVisible(!!session.dirty);
        return session.presentation;
      }
      if (diagramId) {
        var d = diagramById(state, diagramId);
        if (d && titleEl) titleEl.textContent = d.name;
        if (d && metaEl) metaEl.textContent = d.package + " · " + d.kind;
        setDraftVisible(!!state.drafts[String(diagramId)]);
        return getPresentation(state, diagramId);
      }
      return defaultPresentation([], []);
    }

    function initCy(presentation) {
      var els = cyElementsFromPresentation(presentation);
      cy = cytoscape({
        container: document.getElementById("diagram-canvas"),
        elements: els,
        style: [
          {
            selector: "node",
            style: {
              "background-color": "#e7eef7",
              "border-color": "#1f3a5f",
              "border-width": 2,
              label: "data(label)",
              "text-valign": "center",
              shape: "round-rectangle",
              padding: 10,
            },
          },
          {
            selector: "node.draw-source",
            style: { "border-color": "#c9a227", "border-width": 3 },
          },
          {
            selector: "edge",
            style: {
              "line-color": "#5a6478",
              "target-arrow-color": "#5a6478",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              label: "data(label)",
              "font-size": 9,
            },
          },
        ],
        layout: {
          name: els.nodes.length ? "preset" : "grid",
          fit: true,
          padding: 32,
        },
        wheelSensitivity: 0.2,
      });

      cy.on("dragfree", "node", markDirty);
      cy.on("tap", "node", function (evt) {
        var node = evt.target;
        updateEdgePalette(node.data("label"));
        if (!drawMode) return;
        if (!drawSource) {
          drawSource = node;
          node.addClass("draw-source");
          log("relationship draw: pick target", { source: node.id() });
          return;
        }
        if (drawSource.id() === node.id()) return;
        var edgeId = "e" + Date.now();
        cy.add({
          group: "edges",
          data: {
            id: edgeId,
            source: drawSource.id(),
            target: node.id(),
            label: selectedEdgeStereotype,
          },
        });
        drawSource.removeClass("draw-source");
        drawSource = null;
        drawMode = false;
        markDirty();
        log("relationship created", { edgeId: edgeId, stereotype: selectedEdgeStereotype });
      });

      bindTreeToCanvasDrag(cy);
    }

    function modelPosFromClient(cyInstance, clientX, clientY) {
      var rect = cyInstance.container().getBoundingClientRect();
      var renderedX = clientX - rect.left;
      var renderedY = clientY - rect.top;
      var pan = cyInstance.pan();
      var zoom = cyInstance.zoom();
      return {
        x: (renderedX - pan.x) / zoom,
        y: (renderedY - pan.y) / zoom,
      };
    }

    function bindTreeToCanvasDrag(cyInstance) {
      var dropZone = root.querySelector(".yrg-diagram-canvas-wrap");
      if (!dropZone) {
        console.warn(LOG + " drop zone missing");
        return;
      }

      var pointerDrag = null;

      function setDropHighlight(on) {
        dropZone.classList.toggle("yrg-diagram-drop-active", on);
      }

      function pointInCanvas(clientX, clientY) {
        var rect = cyInstance.container().getBoundingClientRect();
        return (
          clientX >= rect.left &&
          clientX <= rect.right &&
          clientY >= rect.top &&
          clientY <= rect.bottom
        );
      }

      function dropLabelAt(clientX, clientY, label) {
        if (!label || !pointInCanvas(clientX, clientY)) {
          return false;
        }
        var modelPos = modelPosFromClient(cyInstance, clientX, clientY);
        addNodeAt(label, modelPos.x, modelPos.y);
        return true;
      }

      root.querySelectorAll(".yrg-tree-item").forEach(function (item) {
        var label = item.getAttribute("data-tree-label") || item.textContent.trim();

        item.addEventListener("mousedown", function (e) {
          if (e.button !== 0) return;
          e.preventDefault();
          pointerDrag = {
            label: label,
            item: item,
            startX: e.clientX,
            startY: e.clientY,
            active: false,
          };
        });

        item.addEventListener("dblclick", function () {
          var extent = cyInstance.extent();
          var cx = (extent.x1 + extent.x2) / 2;
          var cyMid = (extent.y1 + extent.y2) / 2;
          addNodeAt(label, cx + Math.random() * 40 - 20, cyMid + Math.random() * 40 - 20);
          log("tree dblclick add", label);
        });
      });

      document.addEventListener("mousemove", function (e) {
        if (!pointerDrag) return;
        if (!pointerDrag.active) {
          var dx = e.clientX - pointerDrag.startX;
          var dy = e.clientY - pointerDrag.startY;
          if (dx * dx + dy * dy < 25) return;
          pointerDrag.active = true;
          pointerDrag.item.classList.add("yrg-tree-dragging");
          setDropHighlight(pointInCanvas(e.clientX, e.clientY));
          log("tree drag move", pointerDrag.label);
        } else {
          setDropHighlight(pointInCanvas(e.clientX, e.clientY));
        }
      });

      document.addEventListener("mouseup", function (e) {
        if (!pointerDrag) return;
        var payload = pointerDrag;
        pointerDrag = null;
        payload.item.classList.remove("yrg-tree-dragging");
        setDropHighlight(false);
        if (!payload.active) return;
        if (dropLabelAt(e.clientX, e.clientY, payload.label)) {
          log("tree drop added", payload.label);
        }
      });
    }

    function updateEdgePalette(nodeLabel) {
      root.querySelectorAll("[data-edge-stereotype]").forEach(function (btn) {
        var st = btn.getAttribute("data-edge-stereotype");
        var disabled = st === "realizes" && nodeLabel !== "Component";
        btn.disabled = disabled;
        btn.classList.toggle("disabled", disabled);
      });
    }

    function addNodeAt(label, x, y) {
      nextNodeId += 1;
      var id = String(nextNodeId);
      cy.add({
        group: "nodes",
        data: { id: id, label: label },
        position: { x: x, y: y },
      });
      markDirty();
      log("node added", { id: id, label: label });
    }

    root.querySelectorAll("[data-element-stereotype]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var label = "New " + btn.getAttribute("data-element-stereotype");
        addNodeAt(label, 200 + Math.random() * 80, 150 + Math.random() * 80);
      });
    });

    root.querySelectorAll("[data-edge-stereotype]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (btn.disabled) return;
        selectedEdgeStereotype = btn.getAttribute("data-edge-stereotype");
        drawMode = true;
        drawSource = null;
        cy.nodes(".draw-source").removeClass("draw-source");
        log("relationship stereotype selected", selectedEdgeStereotype);
        showToast("Click source node, then target", "info");
      });
    });

    var addRelBtn = root.querySelector('[data-testid="diagram-node-add-rel"]');
    if (addRelBtn) {
      addRelBtn.addEventListener("click", function () {
        drawMode = true;
        drawSource = null;
        log("relationship draw mode");
        showToast("Click source node, then target", "info");
      });
    }

    root.querySelector('[data-testid="diagram-save-btn"]').addEventListener("click", function () {
      var pres = presentationFromCy(cy);
      if (mode === "create" && sessionId) {
        updateCreateSession(state, sessionId, pres);
        var created = commitCreateSession(state, sessionId);
        if (created) window.location.href = listUrl("saved=1");
        return;
      }
      if (diagramId) {
        commitDiagram(state, diagramId, pres);
        window.location.href = listUrl("saved=1");
      }
    });

    root.querySelector('[data-testid="diagram-discard-btn"]').addEventListener("click", function () {
      var hasDraft =
        (mode === "create" &&
          sessionId &&
          getCreateSession(state, sessionId) &&
          getCreateSession(state, sessionId).dirty) ||
        (diagramId && state.drafts[String(diagramId)]);
      if (hasDraft && !window.confirm("Discard unsaved draft changes?")) return;
      if (mode === "create" && sessionId) {
        discardCreateSession(state, sessionId);
      } else if (diagramId) {
        clearDraft(state, diagramId);
      }
      window.location.href = listUrl("discarded=1");
    });

    var createForm = document.getElementById("diagramCreateForm");
    if (createForm) {
      createForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var name = document.getElementById("diagramName").value.trim();
        var pkg = document.getElementById("diagramPackage").value;
        var kind = document.getElementById("diagramKind").value;
        var sid = createSession(state, { name: name, package: pkg, kind: kind });
        var createUrl = config.urls.create || "/mockups/diagram/create/";
        window.location.href = createUrl + "?session=" + encodeURIComponent(sid);
      });
    }

    initCy(loadPresentation());
    log("editor ready", { mode: mode, diagramId: diagramId, sessionId: sessionId });
  }

  /* ── VIEW BROWSER — Add Diagram modal ─────────────────────────── */

  function initBrowseAddDiagram() {
    var form = document.getElementById("addDiagramForm");
    if (!form) return;
    var seed = parseJson("mock-diagram-seed", { diagrams: [], presentations: {} });
    var config = parseJson("mock-diagram-browse-config", {});
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var state = getStore(seed);
      var name = document.getElementById("addDiagramName").value.trim() || "Untitled Diagram";
      var pkg = document.getElementById("addDiagramPackage").value;
      var kind = document.getElementById("addDiagramKind").value;
      var sid = createSession(state, { name: name, package: pkg, kind: kind });
      var createUrl = config.urls.create || "/mockups/diagram/create/";
      log("browse Add Diagram → create session", sid);
      window.location.href = createUrl + "?session=" + encodeURIComponent(sid);
    });
  }

  /** Public helper for browse modal (legacy onclick fallback). */
  window.mockupDiagramCreateFromBrowse = function () {
    var form = document.getElementById("addDiagramForm");
    if (form) form.requestSubmit();
  };

  document.addEventListener("DOMContentLoaded", function () {
    initListPage();
    initEditorPage();
    initBrowseAddDiagram();
  });
})();
