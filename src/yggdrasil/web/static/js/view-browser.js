/**
 * View Browser — table/graph modes, panel toggles, cytoscape selection.
 * Behaviour aligned with mockups/view/browse.html.
 */
(function () {
  'use strict';

  var PANEL_ANIM_MS = 220;

  var selectedElementId = null;

  function getRoot() {
    return document.getElementById('browserRoot');
  }

  function getGraphUrl() {
    var root = getRoot();
    var base = root && root.getAttribute('data-graph-url');
    if (!base) {
      return window.viewBrowseGraphUrl || null;
    }
    var params = new URLSearchParams(window.location.search);
    params.delete('view');
    params.delete('partial');
    var qs = params.toString();
    return qs ? base + '?' + qs : base;
  }

  function isGraphMode() {
    var root = getRoot();
    return !!(root && root.classList.contains('yrg-mode-graph'));
  }

  function syncBrowseUrl(params) {
    var qs = params.toString();
    var url = window.location.pathname + (qs ? '?' + qs : '');
    window.history.replaceState(null, '', url);
  }

  function updateDepthBadge(slider) {
    var badge = document.querySelector('[data-testid="browser-depth-value"]');
    if (badge && slider) {
      badge.textContent = slider.value + ' / ' + slider.max;
    }
  }

  function syncFilterFormDepth(depth) {
    var input = document.querySelector('#filterForm input[name="depth"]');
    if (input) {
      input.value = depth;
    }
  }

  function updateElementCountLabel() {
    var container = document.getElementById('results-container');
    var countEl = document.getElementById('browserElementCount');
    if (!container || !countEl) {
      return;
    }
    var count = container.getAttribute('data-element-count');
    if (count !== null) {
      countEl.textContent = count + ' elements';
    }
  }

  function refreshResultsContainer(params) {
    var fetchParams = new URLSearchParams(params.toString());
    fetchParams.set('partial', 'results');
    var url = window.location.pathname + '?' + fetchParams.toString();
    return fetch(url, { headers: { Accept: 'text/html' } })
      .then(function (r) {
        if (!r.ok) {
          throw new Error('results partial failed status=' + r.status);
        }
        return r.text();
      })
      .then(function (html) {
        var container = document.getElementById('results-container');
        if (!container) {
          return;
        }
        var temp = document.createElement('div');
        temp.innerHTML = html.trim();
        var fresh = temp.firstElementChild;
        if (fresh) {
          container.replaceWith(fresh);
        }
        updateElementCountLabel();
        console.log('[view-browser] results container refreshed');
      })
      .catch(function (err) {
        console.error('[view-browser] results refresh failed', err);
      });
  }

  function resetFilterFormFields() {
    var form = document.getElementById('filterForm');
    if (!form) {
      return;
    }
    form.querySelectorAll('select').forEach(function (sel) {
      sel.selectedIndex = 0;
    });
    form.querySelectorAll('input[type="date"]').forEach(function (inp) {
      inp.value = '';
    });
    var viewInput = document.getElementById('filterViewMode');
    if (viewInput) {
      viewInput.value = isGraphMode() ? 'graph' : 'table';
    }
    syncFilterFormDepth('1');
  }

  function buildParamsAfterClear() {
    var params = new URLSearchParams();
    if (isGraphMode()) {
      params.set('mode', 'graph');
    }
    return params;
  }

  function applyClearFilters(evt) {
    if (evt && evt.preventDefault) {
      evt.preventDefault();
    }
    var params = buildParamsAfterClear();
    params.delete('partial');
    var slider = document.getElementById('depthSlider');
    if (slider) {
      slider.value = slider.min || '1';
      updateDepthBadge(slider);
    }
    resetFilterFormFields();
    syncBrowseUrl(params);
    Promise.all([
      refreshNavigatorTree(params),
      refreshResultsContainer(params)
    ]).then(function () {
      if (isGraphMode()) {
        replotGraph();
        clearSelection();
      }
      console.log(
        '[view-browser] filters cleared in-place mode=%s',
        isGraphMode() ? 'graph' : 'table'
      );
    });
  }

  function refreshNavigatorTree(params) {
    var fetchParams = new URLSearchParams(params.toString());
    fetchParams.set('partial', 'navigator');
    fetchParams.delete('view');
    var url = window.location.pathname + '?' + fetchParams.toString();
    return fetch(url, { headers: { Accept: 'text/html' } })
      .then(function (r) {
        if (!r.ok) {
          throw new Error('navigator partial failed status=' + r.status);
        }
        return r.text();
      })
      .then(function (html) {
        var tree = document.getElementById('elementTree');
        if (tree) {
          tree.innerHTML = html;
        }
        console.log('[view-browser] navigator tree refreshed');
      })
      .catch(function (err) {
        console.error('[view-browser] navigator refresh failed', err);
      });
  }

  function applyDepthChange(slider) {
    var params = new URLSearchParams(window.location.search);
    params.set('depth', slider.value);
    params.delete('partial');
    if (isGraphMode()) {
      params.set('mode', 'graph');
      syncBrowseUrl(params);
      updateDepthBadge(slider);
      syncFilterFormDepth(slider.value);
      refreshNavigatorTree(params);
      replotGraph();
      clearSelection();
      console.log('[view-browser] depth=%s applied in graph mode (in-place)', slider.value);
      return;
    }
    window.location.search = params.toString();
  }

  function scheduleGraphResize() {
    if (!window.cyInstance) {
      return;
    }
    setTimeout(function () {
      window.cyInstance.resize();
      window.cyInstance.fit(undefined, 40);
    }, PANEL_ANIM_MS);
  }

  function syncPanelTogglePositions() {
    var root = getRoot();
    var nav = document.getElementById('browserNavPanel');
    var insp = document.getElementById('browserInspectorPanel');
    if (!root) {
      return;
    }
    root.classList.toggle('nav-collapsed', !!(nav && nav.classList.contains('collapsed')));
    root.classList.toggle('inspector-collapsed', !!(insp && insp.classList.contains('collapsed')));
  }

  var FIELD_SCHEMA = {
    system: [{ path: 'name', label: 'Name' }, { path: 'owner', label: 'Owner' }, { path: 'package', label: 'Package' }],
    container: [{ path: 'name', label: 'Name' }, { path: 'owner', label: 'Owner' }, { path: 'health', label: 'Health' }, { path: 'properties.version', label: 'Version' }],
    component: [{ path: 'name', label: 'Name' }, { path: 'owner', label: 'Owner' }, { path: 'health', label: 'Health' }, { path: 'properties.version', label: 'Version' }, { path: 'properties.jira_key', label: 'Jira key' }],
    person: [{ path: 'name', label: 'Name' }, { path: 'package', label: 'Package' }],
    depends_on: [{ path: 'stereotype', label: 'Stereotype' }, { path: 'properties.protocol', label: 'Protocol' }],
    calls: [{ path: 'stereotype', label: 'Stereotype' }, { path: 'properties.protocol', label: 'Protocol' }],
    uses: [{ path: 'stereotype', label: 'Stereotype' }]
  };

  function readLoadedViewport() {
    var el = document.getElementById('loaded-viewport');
    if (!el || !el.textContent) {
      return null;
    }
    try {
      return JSON.parse(el.textContent);
    } catch (err) {
      return null;
    }
  }

  function readMultiSelect(id) {
    var sel = document.getElementById(id);
    if (!sel) {
      return [];
    }
    return Array.prototype.filter.call(sel.selectedOptions, function (opt) {
      return opt.value;
    }).map(function (opt) {
      return opt.value;
    });
  }

  function readFieldMapFromForm() {
    var map = {};
    document.querySelectorAll('.view-field-section').forEach(function (section) {
      var slug = section.dataset.stereotype;
      if (!slug) {
        return;
      }
      var checked = [];
      section.querySelectorAll('.view-field-checkbox:checked').forEach(function (input) {
        checked.push(input.value);
      });
      if (checked.length) {
        map[slug] = checked;
      }
    });
    return map;
  }

  function buildSectionHtml(kind, slug, checkedPaths) {
    var fields = FIELD_SCHEMA[slug] || [{ path: 'name', label: 'Name' }];
    var defaultChecked = fields.map(function (field) { return field.path; });
    var checkedSet = {};
    (checkedPaths && checkedPaths.length ? checkedPaths : defaultChecked).forEach(function (path) {
      checkedSet[path] = true;
    });
    var label = kind === 'element'
      ? slug.replace(/_/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); })
      : slug.replace(/_/g, ' ');
    var checks = fields.map(function (field, idx) {
      var checkedAttr = checkedSet[field.path] ? ' checked' : '';
      return (
        '<div class="form-check">' +
        '<input class="form-check-input view-field-checkbox" type="checkbox" ' +
        'name="field_' + slug + '" value="' + field.path + '" ' +
        'id="field-' + slug + '-' + idx + '" ' +
        'data-testid="view-field-' + slug + '-' + field.path + '"' + checkedAttr + '>' +
        '<label class="form-check-label" for="field-' + slug + '-' + idx + '">' + field.label + '</label>' +
        '</div>'
      );
    }).join('');
    return (
      '<div class="mt-3 view-field-section" data-stereotype="' + slug + '" data-kind="' + kind + '" ' +
      'data-testid="view-fields-' + slug + '">' +
      '<span class="form-label d-block" style="font-size:0.78rem;font-weight:600;">' +
      label + ' — visible fields</span>' +
      '<div class="d-flex flex-wrap gap-3">' + checks + '</div></div>'
    );
  }

  function renderFieldSections() {
    var container = document.getElementById('viewFieldSections');
    if (!container) {
      return;
    }
    var existingMap = readFieldMapFromForm();
    var elementSts = readMultiSelect('filter-stereotype');
    var relSts = readMultiSelect('filter-edge-stereotype');
    if (!elementSts.length && !relSts.length) {
      container.innerHTML =
        '<p class="small text-muted mt-2 mb-0" data-testid="view-field-sections-empty">' +
        'Select element or relationship stereotypes to configure visible fields.</p>';
      return;
    }
    var html = '';
    elementSts.forEach(function (slug) {
      html += buildSectionHtml('element', slug, existingMap[slug]);
    });
    relSts.forEach(function (slug) {
      html += buildSectionHtml('relationship', slug, existingMap[slug]);
    });
    container.innerHTML = html;
  }

  function captureViewport() {
    var cy = window.cyInstance;
    if (!cy) {
      return null;
    }
    var payload = { zoom: cy.zoom(), pan: cy.pan() };
    if (selectedElementId) {
      var node = cy.getElementById(String(selectedElementId));
      if (node.length) {
        var row = node.data('label') || '';
        var slugMatch = row.match(/Name:\s*(\S+)/);
        payload.center_element_id = slugMatch ? slugMatch[1] : String(selectedElementId);
      }
    }
    return payload;
  }

  function restoreViewport(viewport) {
    var cy = window.cyInstance;
    if (!cy || !viewport) {
      return;
    }
    if (typeof viewport.zoom === 'number') {
      cy.zoom(viewport.zoom);
    }
    if (viewport.pan) {
      cy.pan(viewport.pan);
    }
    if (viewport.center_element_id) {
      var node = cy.nodes().filter(function (n) {
        return String(n.data('label') || '').toLowerCase().indexOf(String(viewport.center_element_id).toLowerCase()) >= 0;
      });
      if (node.length) {
        cy.center(node);
      }
    }
    console.log('[view-browser] restored viewport from saved View');
  }

  function populateSaveFormHiddenFields() {
    var container = document.getElementById('saveViewHiddenFields');
    if (!container) {
      return;
    }
    container.innerHTML = '';
    readMultiSelect('filter-package').forEach(function (value) {
      container.innerHTML += '<input type="hidden" name="package" value="' + value + '">';
    });
    readMultiSelect('filter-stereotype').forEach(function (value) {
      container.innerHTML += '<input type="hidden" name="stereotype" value="' + value + '">';
    });
    readMultiSelect('filter-edge-stereotype').forEach(function (value) {
      container.innerHTML += '<input type="hidden" name="edge_stereotype" value="' + value + '">';
    });
    var fieldMap = readFieldMapFromForm();
    Object.keys(fieldMap).forEach(function (slug) {
      fieldMap[slug].forEach(function (path) {
        container.innerHTML += '<input type="hidden" name="field_' + slug + '" value="' + path + '">';
      });
    });
    var depthInput = document.getElementById('saveViewDepthInput');
    var slider = document.getElementById('depthSlider');
    if (depthInput && slider) {
      depthInput.value = slider.value;
    }
    var includeViewport = document.getElementById('saveViewIncludeViewport');
    if (includeViewport && includeViewport.checked) {
      var viewport = captureViewport();
      if (viewport) {
        container.innerHTML += '<input type="hidden" name="viewport" value=\'' +
          JSON.stringify(viewport).replace(/'/g, '&#39;') + '\'>';
      }
    }
  }

  function bindFilterPanelControls() {
    ['filter-package', 'filter-stereotype', 'filter-edge-stereotype'].forEach(function (id) {
      var sel = document.getElementById(id);
      if (sel) {
        sel.addEventListener('change', renderFieldSections);
      }
    });
    var saveForm = document.getElementById('saveViewForm');
    if (saveForm) {
      saveForm.addEventListener('submit', populateSaveFormHiddenFields);
    }
  }

  function cytoscapeStyles() {
    return [
      {
        selector: 'node',
        style: {
          label: 'data(label)',
          'font-size': 8,
          'text-wrap': 'wrap',
          'text-max-width': '120px',
          'text-valign': 'center',
          'text-halign': 'center',
          'background-color': 'var(--yrg-node-fill)',
          'border-color': 'var(--yrg-node-stroke)',
          'border-width': 2,
          width: 56,
          height: 56,
          shape: 'round-rectangle'
        }
      },
      {
        selector: 'node[stereotype = "System"]',
        style: { shape: 'round-rectangle', width: 48, height: 36 }
      },
      {
        selector: 'node[stereotype = "Person"]',
        style: { shape: 'ellipse', 'background-color': '#e8f4ea' }
      },
      {
        selector: 'node:selected',
        style: {
          'border-color': 'var(--hg-accent)',
          'border-width': 3,
          'background-color': '#fff8e1'
        }
      },
      {
        selector: 'edge',
        style: {
          width: 2,
          'line-color': 'var(--yrg-edge-stroke)',
          'target-arrow-color': 'var(--yrg-edge-stroke)',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'font-size': 8,
          label: 'data(label)',
          'text-rotation': 'autorotate'
        }
      },
      {
        selector: 'edge:selected',
        style: {
          'line-color': 'var(--hg-accent)',
          'target-arrow-color': 'var(--hg-accent)',
          width: 3
        }
      }
    ];
  }

  function bindGraphEvents(cy) {
    cy.on('tap', 'node', function (evt) {
      var rawId = evt.target.data('id');
      selectElement(parseInt(rawId, 10));
    });
    cy.on('tap', 'edge', function (evt) {
      var rawId = evt.target.data('id');
      selectRelationship(parseInt(rawId, 10));
    });
    cy.on('tap', function (evt) {
      if (evt.target === cy) {
        clearSelection();
      }
    });
  }

  function updateGraphNodeCount(count) {
    var badge = document.querySelector('[data-testid="graph-node-count"]');
    if (badge) {
      badge.textContent = count + ' nodes';
    }
  }

  function replotGraph() {
    if (window.cyInstance) {
      window.cyInstance.destroy();
      window.cyInstance = null;
    }
    var cyEl = document.getElementById('cy');
    if (cyEl) {
      cyEl.removeAttribute('data-testid');
      cyEl.innerHTML = '';
    }
    loadGraph(true);
    console.log('[view-browser] graph replot requested');
  }

  function loadGraph(forceReload) {
    var url = getGraphUrl();
    if (!url) {
      return;
    }
    if (window.cyInstance && !forceReload) {
      window.cyInstance.resize();
      return;
    }
    fetch(url, { headers: { Accept: 'application/json' } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var cyEl = document.getElementById('cy');
        if (!cyEl) {
          return;
        }
        cyEl.setAttribute('data-testid', 'graph-json-loaded');
        var nodes = (data.elements || []).map(function (n) {
          return { group: 'nodes', data: n.data };
        });
        var edges = (data.edges || []).map(function (e) {
          return { group: 'edges', data: e.data };
        });
        window.cyInstance = cytoscape({
          container: cyEl,
          elements: nodes.concat(edges),
          style: cytoscapeStyles(),
          layout: { name: 'grid', animate: false, padding: 40 },
          minZoom: 0.2,
          maxZoom: 3
        });
        window.cyInstance.fit(undefined, 40);
        restoreViewport(readLoadedViewport());
        bindGraphEvents(window.cyInstance);
        updateGraphNodeCount(nodes.length);
        console.log('[view-browser] graph loaded nodes=%s edges=%s', nodes.length, edges.length);
      })
      .catch(function (err) {
        console.error('[view-browser] graph load failed', err);
      });
  }

  function inspectorUrl(kind, id) {
    var root = getRoot();
    var attr = kind === 'relationship' ? 'data-inspector-relationship-url' : 'data-inspector-element-url';
    var pattern = root && root.getAttribute(attr);
    if (!pattern) {
      return null;
    }
    return pattern.replace('/0/', '/' + String(id) + '/');
  }

  function showInspectorEmpty() {
    var empty = document.getElementById('inspectorEmpty');
    var content = document.getElementById('inspectorContent');
    if (empty) {
      empty.classList.remove('d-none');
    }
    if (content) {
      content.classList.add('d-none');
      content.innerHTML = '';
    }
  }

  function showInspectorHtml(html) {
    var empty = document.getElementById('inspectorEmpty');
    var content = document.getElementById('inspectorContent');
    if (!content) {
      return;
    }
    content.innerHTML = html;
    content.classList.remove('d-none');
    if (empty) {
      empty.classList.add('d-none');
    }
  }

  function loadElementInspector(id) {
    var url = inspectorUrl('element', id);
    if (!url) {
      return;
    }
    fetch(url, { headers: { Accept: 'text/html' } })
      .then(function (r) {
        if (!r.ok) {
          throw new Error('inspector element load failed status=' + r.status);
        }
        return r.text();
      })
      .then(showInspectorHtml)
      .catch(function (err) {
        console.error('[view-browser] element inspector load failed id=%s', id, err);
        showInspectorEmpty();
      });
  }

  function loadRelationshipInspector(id) {
    var url = inspectorUrl('relationship', id);
    if (!url) {
      return;
    }
    fetch(url, { headers: { Accept: 'text/html' } })
      .then(function (r) {
        if (!r.ok) {
          throw new Error('inspector relationship load failed status=' + r.status);
        }
        return r.text();
      })
      .then(showInspectorHtml)
      .catch(function (err) {
        console.error('[view-browser] relationship inspector load failed id=%s', id, err);
        showInspectorEmpty();
      });
  }

  function bindInspectorInteractions() {
    var body = document.getElementById('inspectorBody');
    if (!body) {
      return;
    }
    body.addEventListener('click', function (evt) {
      var relRow = evt.target.closest('[data-relationship-id]');
      if (relRow) {
        var relId = parseInt(relRow.getAttribute('data-relationship-id'), 10);
        selectRelationship(relId);
        return;
      }
      var endpoint = evt.target.closest('[data-element-id]');
      if (endpoint && endpoint.closest('#inspectorContent')) {
        var elId = parseInt(endpoint.getAttribute('data-element-id'), 10);
        selectElement(elId);
      }
    });
  }

  function highlightNavItem(id) {
    document.querySelectorAll('.yrg-element-item').forEach(function (btn) {
      var elId = parseInt(btn.getAttribute('data-element-id'), 10);
      btn.classList.toggle('active', elId === id);
    });
  }

  function clearSelection() {
    selectedElementId = null;
    document.querySelectorAll('.yrg-element-item').forEach(function (btn) {
      btn.classList.remove('active');
    });
    if (window.cyInstance) {
      window.cyInstance.elements().unselect();
    }
    showInspectorEmpty();
    console.log('[view-browser] selection cleared');
  }

  function selectElement(id) {
    if (!id || Number.isNaN(id)) {
      return;
    }
    selectedElementId = id;
    highlightNavItem(id);
    if (window.cyInstance) {
      window.cyInstance.elements().unselect();
      var node = window.cyInstance.getElementById(String(id));
      if (node.length) {
        node.select();
        window.cyInstance.animate({ center: { eles: node }, zoom: 1.2 }, { duration: 200 });
      }
    }
    loadElementInspector(id);
    console.log('[view-browser] element selected id=%s', id);
  }

  function selectRelationship(id) {
    if (!id || Number.isNaN(id)) {
      return;
    }
    selectedElementId = null;
    document.querySelectorAll('.yrg-element-item').forEach(function (btn) {
      btn.classList.remove('active');
    });
    if (window.cyInstance) {
      window.cyInstance.elements().unselect();
      var edge = window.cyInstance.getElementById(String(id));
      if (edge.length) {
        edge.select();
      }
    }
    loadRelationshipInspector(id);
    console.log('[view-browser] relationship selected id=%s', id);
  }

  function setView(mode) {
    var root = getRoot();
    var table = document.getElementById('tableView');
    var graph = document.getElementById('graphView');
    var tableBtn = document.getElementById('tableViewBtn');
    var graphBtn = document.getElementById('graphViewBtn');
    var filterView = document.getElementById('filterViewMode');
    if (!root || !table || !graph || !tableBtn || !graphBtn) {
      return;
    }

    var isGraph = mode === 'graph';
    document.body.classList.toggle('yrg-view-browser', isGraph);
    root.classList.toggle('yrg-mode-graph', isGraph);
    root.classList.toggle('yrg-mode-table', !isGraph);
    if (filterView) {
      filterView.value = mode;
    }

    if (isGraph) {
      table.classList.add('d-none');
      graph.classList.remove('d-none');
      graphBtn.classList.add('active');
      tableBtn.classList.remove('active');
      syncPanelTogglePositions();
      loadGraph();
      scheduleGraphResize();
    } else {
      table.classList.remove('d-none');
      graph.classList.add('d-none');
      tableBtn.classList.add('active');
      graphBtn.classList.remove('active');
    }

    var zoomControls = document.getElementById('graphZoomControls');
    if (zoomControls) {
      zoomControls.classList.toggle('d-none', !isGraph);
    }

    var urlParams = new URLSearchParams(window.location.search);
    urlParams.set('mode', mode);
    urlParams.delete('view');
    urlParams.delete('partial');
    syncBrowseUrl(urlParams);

    console.log('[view-browser] mode=%s', mode);
  }

  function bindNavPanelToggle() {
    var nav = document.getElementById('browserNavPanel');
    var btn = document.getElementById('toggleNavBtn');
    if (!nav || !btn) {
      return;
    }
    btn.addEventListener('click', function () {
      nav.classList.toggle('collapsed');
      btn.textContent = nav.classList.contains('collapsed') ? '›' : '‹';
      syncPanelTogglePositions();
      scheduleGraphResize();
    });
  }

  function bindInspectorPanelToggle() {
    var panel = document.getElementById('browserInspectorPanel');
    var btn = document.getElementById('toggleInspectorBtn');
    if (!panel || !btn) {
      return;
    }
    btn.addEventListener('click', function () {
      panel.classList.toggle('collapsed');
      btn.textContent = panel.classList.contains('collapsed') ? '‹' : '›';
      syncPanelTogglePositions();
      scheduleGraphResize();
    });
  }

  function zoomGraph(action) {
    var cy = window.cyInstance;
    if (!cy) {
      return;
    }
    var center = { x: cy.width() / 2, y: cy.height() / 2 };
    if (action === 'in') {
      cy.zoom({ level: cy.zoom() * 1.3, renderedPosition: center });
    } else if (action === 'out') {
      cy.zoom({ level: cy.zoom() / 1.3, renderedPosition: center });
    } else {
      cy.fit(undefined, 40);
    }
    console.log('[view-browser] zoom action=%s', action);
  }

  function bindZoomControls() {
    var replot = document.getElementById('graphReplotBtn');
    var zoomIn = document.getElementById('graphZoomInBtn');
    var zoomOut = document.getElementById('graphZoomOutBtn');
    var zoomFit = document.getElementById('graphZoomFitBtn');
    if (replot) {
      replot.addEventListener('click', function () { replotGraph(); });
    }
    if (zoomIn) {
      zoomIn.addEventListener('click', function () { zoomGraph('in'); });
    }
    if (zoomOut) {
      zoomOut.addEventListener('click', function () { zoomGraph('out'); });
    }
    if (zoomFit) {
      zoomFit.addEventListener('click', function () { zoomGraph('fit'); });
    }
  }

  function bindClearFilters() {
    document.querySelectorAll('[data-action="clear-filters"]').forEach(function (link) {
      link.addEventListener('click', applyClearFilters);
    });
  }

  function bindDepthSlider() {
    var slider = document.getElementById('depthSlider');
    if (!slider) {
      return;
    }
    slider.addEventListener('change', function () {
      applyDepthChange(slider);
    });
  }

  function bindNavigatorSelection() {
    var tree = document.getElementById('elementTree');
    if (!tree) {
      return;
    }
    tree.addEventListener('click', function (evt) {
      var item = evt.target.closest('.yrg-element-item');
      if (!item) {
        return;
      }
      var id = parseInt(item.getAttribute('data-element-id'), 10);
      selectElement(id);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    window.setView = setView;
    window.selectElement = selectElement;
    window.clearSelection = clearSelection;
    window.zoomGraph = zoomGraph;
    window.replotGraph = replotGraph;

    bindNavPanelToggle();
    bindInspectorPanelToggle();
    bindNavigatorSelection();
    bindInspectorInteractions();
    bindZoomControls();
    bindDepthSlider();
    bindClearFilters();
    bindFilterPanelControls();
    syncPanelTogglePositions();

    var root = getRoot();
    var initial = (root && root.getAttribute('data-initial-view')) || 'graph';
    setView(initial);
  });
})();
