// lightbox.js — 본문 이미지 (SVG·PNG) 클릭 시 확대 + 다운로드 링크
// 외부 라이브러리 의존 없음 (vanilla JS, ~3 KB)

document$.subscribe(function () {
  var content = document.querySelector('.md-content article');
  if (!content) return;
  if (content.dataset.lightboxApplied === 'true') return;
  content.dataset.lightboxApplied = 'true';

  // 본문 이미지 (마크다운 ![alt](path) 로 생성된 <img>) 와 inline SVG 모두 대상
  var images = content.querySelectorAll('img:not(.no-zoom), figure svg.zoomable');
  images.forEach(function (img) {
    img.style.cursor = 'zoom-in';
    img.classList.add('lightbox-trigger');
    img.addEventListener('click', function (e) {
      e.preventDefault();
      openLightbox(img);
    });
  });
});

function openLightbox(sourceEl) {
  var overlay = document.createElement('div');
  overlay.className = 'lightbox-overlay';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', '이미지 확대 보기');

  var container = document.createElement('div');
  container.className = 'lightbox-container';

  // 이미지 복제 (원본 DOM 유지)
  var imgClone;
  var src = '';
  var alt = '';
  if (sourceEl.tagName === 'IMG') {
    imgClone = document.createElement('img');
    imgClone.src = sourceEl.src;
    imgClone.alt = sourceEl.alt || '확대 이미지';
    src = sourceEl.src;
    alt = sourceEl.alt || 'image';
  } else {
    // inline SVG → 복제
    imgClone = sourceEl.cloneNode(true);
    imgClone.removeAttribute('width');
    imgClone.removeAttribute('height');
    imgClone.style.maxWidth = '100%';
    imgClone.style.maxHeight = '100%';
    // SVG → data URL 변환 (다운로드용)
    var serializer = new XMLSerializer();
    var svgStr = serializer.serializeToString(sourceEl);
    src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgStr);
    alt = sourceEl.getAttribute('aria-label') || 'illustration';
  }
  imgClone.classList.add('lightbox-image');

  // 줌·팬 상태 + 인터랙션 (휠 줌 + drag pan + 클릭 토글 1x→2x→3x→1x)
  var state = { zoom: 1, x: 0, y: 0, dragging: false, startX: 0, startY: 0 };
  var ZOOM_LEVELS = [1, 2, 3, 5];

  function applyTransform() {
    imgClone.style.transform = 'translate(' + state.x + 'px, ' + state.y + 'px) scale(' + state.zoom + ')';
    imgClone.style.cursor = state.zoom > 1 ? (state.dragging ? 'grabbing' : 'grab') : 'zoom-in';
  }

  // 클릭 → 다음 줌 단계 (1 → 2 → 3 → 5 → 1 cycle)
  imgClone.addEventListener('click', function (e) {
    if (state.dragging) return; // drag 직후 클릭 무시
    e.stopPropagation();
    var idx = ZOOM_LEVELS.indexOf(state.zoom);
    state.zoom = ZOOM_LEVELS[(idx + 1) % ZOOM_LEVELS.length];
    if (state.zoom === 1) { state.x = 0; state.y = 0; }
    applyTransform();
    updateZoomBadge();
  });

  // 휠 → 부드러운 줌 (0.5x ~ 8x)
  imgClone.addEventListener('wheel', function (e) {
    e.preventDefault();
    var delta = e.deltaY < 0 ? 1.15 : 1 / 1.15;
    var newZoom = Math.max(0.5, Math.min(8, state.zoom * delta));
    state.zoom = newZoom;
    if (state.zoom <= 1.01) { state.x = 0; state.y = 0; }
    applyTransform();
    updateZoomBadge();
  }, { passive: false });

  // drag pan (줌 1x 초과 시)
  imgClone.addEventListener('mousedown', function (e) {
    if (state.zoom <= 1) return;
    e.preventDefault();
    state.dragging = true;
    state.startX = e.clientX - state.x;
    state.startY = e.clientY - state.y;
    applyTransform();
  });
  document.addEventListener('mousemove', function (e) {
    if (!state.dragging) return;
    state.x = e.clientX - state.startX;
    state.y = e.clientY - state.startY;
    applyTransform();
  });
  document.addEventListener('mouseup', function () {
    if (state.dragging) {
      state.dragging = false;
      applyTransform();
      // 약간 지연 후 dragging 플래그 해제 (click 이벤트 무시 위해)
      setTimeout(function () { state.dragging = false; }, 50);
    }
  });

  container.appendChild(imgClone);

  // 액션 바 — 줌 배지·다운로드·닫기
  var actions = document.createElement('div');
  actions.className = 'lightbox-actions';

  var zoomBadge = document.createElement('span');
  zoomBadge.className = 'lightbox-zoom-badge';
  function updateZoomBadge() {
    zoomBadge.textContent = '🔍 ' + (state.zoom * 100).toFixed(0) + '%';
  }
  updateZoomBadge();
  actions.appendChild(zoomBadge);

  var resetBtn = document.createElement('button');
  resetBtn.className = 'lightbox-btn';
  resetBtn.textContent = '⊙ 1x';
  resetBtn.title = '줌 초기화 (100%)';
  resetBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    state.zoom = 1; state.x = 0; state.y = 0;
    applyTransform();
    updateZoomBadge();
  });
  actions.appendChild(resetBtn);

  var downloadBtn = document.createElement('a');
  downloadBtn.className = 'lightbox-btn lightbox-btn--download';
  downloadBtn.href = src;
  downloadBtn.download = sanitizeFilename(alt) + extensionFor(src);
  downloadBtn.textContent = '⬇ 다운로드';
  downloadBtn.title = '원본 해상도 다운로드 (SVG = 무한 확대 가능)';
  actions.appendChild(downloadBtn);

  var closeBtn = document.createElement('button');
  closeBtn.className = 'lightbox-btn lightbox-btn--close';
  closeBtn.textContent = '✕ 닫기';
  closeBtn.setAttribute('aria-label', '닫기');
  closeBtn.addEventListener('click', closeLightbox);
  actions.appendChild(closeBtn);

  container.appendChild(actions);

  // 사용 안내 (1 회성)
  var hint = document.createElement('div');
  hint.className = 'lightbox-hint';
  hint.textContent = '💡 클릭 = 줌 단계 (1x → 2x → 3x → 5x) · 휠 = 부드러운 줌 · 드래그 = 이동 · ESC = 닫기';
  container.appendChild(hint);

  overlay.appendChild(container);
  document.body.appendChild(overlay);
  document.body.style.overflow = 'hidden';

  applyTransform();

  // overlay 클릭 (이미지 외부) → 닫기
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) closeLightbox();
  });

  // ESC 키 → 닫기
  document.addEventListener('keydown', escHandler);

  function closeLightbox() {
    overlay.remove();
    document.body.style.overflow = '';
    document.removeEventListener('keydown', escHandler);
  }

  function escHandler(e) {
    if (e.key === 'Escape') closeLightbox();
  }
}

function sanitizeFilename(name) {
  return (name || 'image').replace(/[^a-zA-Z0-9가-힣_\-]+/g, '-').slice(0, 60);
}

function extensionFor(src) {
  if (src.indexOf('image/svg') >= 0) return '.svg';
  if (src.endsWith('.png')) return '.png';
  if (src.endsWith('.jpg') || src.endsWith('.jpeg')) return '.jpg';
  if (src.endsWith('.webp')) return '.webp';
  return '';
}
