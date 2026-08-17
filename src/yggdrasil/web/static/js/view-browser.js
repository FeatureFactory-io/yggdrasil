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

  function refreshNavigatorTree(params) {
    var fetchParams = new URLSearchParams(params.toString());
    fetchParams.set('partial', 'navigator');
    fetchParams.delete('view');
    var url = window.location.pathname + '?' + fetchParams.toString();
    fetch(url, { headers: { Accept: 'text/html' } })
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
        console.log('[view-browser] navigator tree refreshed for depth=%s', params.get('depth'));
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
      params.set('view', 'graph');
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

  function cytoscapeStyles() {
    return [
      {
        selector: 'node',
        style: {
          label: 'data(label)',
          'font-size': 9,
          'text-valign': 'bottom',
          'text-margin-y': 4,
          'background-color': 'var(--yrg-node-fill)',
          'border-color': 'var(--yrg-node-stroke)',
          'border-width': 2,
          width: 36,
          height: 36
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
          layout: { name: 'cose', animate: false, padding: 40 },
          minZoom: 0.2,
          maxZoom: 3
        });
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
    urlParams.set('view', mode);
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
    syncPanelTogglePositions();

    var root = getRoot();
    var initial = root && root.getAttribute('data-initial-view') === 'graph' ? 'graph' : 'table';
    setView(initial);
  });
})();
