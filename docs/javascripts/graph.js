// graph.js — D3 force-directed cross-reference 그래프
// 데이터: data/crossref.json (build_crossref hook 자동 생성)
// 컨테이너: <div id="crossref-graph"></div> (graph.md 페이지)
// 구현: vanilla DOM API (innerHTML 미사용 — XSS 안전)

document$.subscribe(function () {
  var container = document.getElementById('crossref-graph');
  if (!container) return;
  if (typeof d3 === 'undefined') {
    container.replaceChildren();
    var msg = document.createElement('p');
    msg.style.color = '#C62828';
    msg.textContent = '⚠ D3.js 가 로드되지 않았습니다. 새로고침하거나 인터넷 연결을 확인하세요.';
    container.appendChild(msg);
    return;
  }
  if (container.dataset.graphRendered === 'true') return;
  container.dataset.graphRendered = 'true';

  // 데이터 로드 — site root 또는 GitHub Pages prefix 시도
  fetch('/ai-docs-for-biz/data/crossref.json').then(function (r) {
    if (r.ok) return r.json();
    return fetch('data/crossref.json').then(function (r2) { return r2.json(); });
  }).catch(function () {
    return fetch('data/crossref.json').then(function (r) { return r.json(); });
  }).then(function (data) {
    renderGraph(container, data);
  }).catch(function (err) {
    container.replaceChildren();
    var errMsg = document.createElement('p');
    errMsg.style.color = '#C62828';
    errMsg.textContent = '⚠ crossref.json 로드 실패: ' + (err && err.message ? err.message : 'unknown');
    container.appendChild(errMsg);
  });
});

function renderGraph(container, data) {
  var width = container.clientWidth || 900;
  var height = 600;

  var groupColors = {
    track: '#1565C0',
    pkg: '#F57F17',
    guide: '#00695C',
    scenario: '#6A1B9A',
    module: '#C62828',
    other: '#5D4037',
    meta: '#455A64',
  };

  container.replaceChildren();

  var svg = d3.select(container).append('svg')
    .attr('viewBox', [0, 0, width, height])
    .attr('class', 'crossref-graph-svg')
    .attr('role', 'img')
    .attr('aria-label', 'Cross-reference 인터랙티브 그래프');

  var defs = svg.append('defs');
  defs.append('marker')
    .attr('id', 'arrow')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 18)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999')
      .attr('opacity', 0.6);

  var simulation = d3.forceSimulation(data.nodes)
    .force('link', d3.forceLink(data.edges).id(function (d) { return d.id; }).distance(80).strength(0.4))
    .force('charge', d3.forceManyBody().strength(-220))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(28));

  var link = svg.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(data.edges)
    .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.4)
      .attr('stroke-width', function (d) { return Math.sqrt(d.weight) * 1.2; })
      .attr('marker-end', 'url(#arrow)');

  var node = svg.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(data.nodes)
    .join('g')
      .attr('class', 'node')
      .style('cursor', 'pointer')
      .call(drag(simulation));

  node.append('circle')
    .attr('r', function (d) { return 6 + Math.min(8, countDegree(d, data.edges)); })
    .attr('fill', function (d) { return groupColors[d.group] || '#999'; })
    .attr('stroke', 'white')
    .attr('stroke-width', 2);

  node.append('text')
    .attr('dx', 10)
    .attr('dy', 4)
    .attr('font-size', '10px')
    .attr('font-family', 'Pretendard, sans-serif')
    .attr('fill', '#333')
    .style('pointer-events', 'none')
    .text(function (d) { return d.label; });

  node.append('title')
    .text(function (d) {
      var deg = countDegree(d, data.edges);
      return d.label + '\n' + d.group_label + '\n인용 연결 ' + deg + ' 회';
    });

  node.on('click', function (event, d) {
    if (event.defaultPrevented) return;
    window.location.href = d.url;
  });

  simulation.on('tick', function () {
    link
      .attr('x1', function (d) { return d.source.x; })
      .attr('y1', function (d) { return d.source.y; })
      .attr('x2', function (d) { return d.target.x; })
      .attr('y2', function (d) { return d.target.y; });
    node.attr('transform', function (d) { return 'translate(' + d.x + ',' + d.y + ')'; });
  });

  // 통계 정보 — 안전한 DOM API 사용
  var statsBox = document.createElement('div');
  statsBox.className = 'crossref-stats';
  var strong = document.createElement('strong');
  strong.textContent = '📊 그래프 통계: ';
  statsBox.appendChild(strong);
  statsBox.appendChild(document.createTextNode(
    '노드 ' + data.stats.node_count + ' · 엣지 ' + data.stats.edge_count +
    ' · 총 인용 ' + data.stats.total_citations + ' 회 '
  ));
  var hint = document.createElement('span');
  hint.style.opacity = '0.7';
  hint.textContent = '(노드 클릭 → 페이지 이동, 드래그 가능)';
  statsBox.appendChild(hint);
  container.appendChild(statsBox);

  // 범례 — 안전한 DOM API 사용
  var legend = document.createElement('div');
  legend.className = 'crossref-legend';
  Object.keys(groupColors).forEach(function (key) {
    var label = data.nodes.find(function (n) { return n.group === key; });
    if (!label) return;
    var item = document.createElement('span');
    item.className = 'legend-item';
    var dot = document.createElement('span');
    dot.className = 'legend-dot';
    dot.style.backgroundColor = groupColors[key];
    item.appendChild(dot);
    item.appendChild(document.createTextNode(label.group_label));
    legend.appendChild(item);
  });
  container.appendChild(legend);
}

function countDegree(node, edges) {
  var count = 0;
  for (var i = 0; i < edges.length; i++) {
    var s = edges[i].source;
    var t = edges[i].target;
    var sId = (typeof s === 'object' && s !== null) ? s.id : s;
    var tId = (typeof t === 'object' && t !== null) ? t.id : t;
    if (sId === node.id) count++;
    if (tId === node.id) count++;
  }
  return count;
}

function drag(simulation) {
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }
  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }
  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }
  return d3.drag()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended);
}
