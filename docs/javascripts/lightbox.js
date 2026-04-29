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
  container.appendChild(imgClone);

  // 액션 바 — 다운로드·닫기
  var actions = document.createElement('div');
  actions.className = 'lightbox-actions';

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
  overlay.appendChild(container);
  document.body.appendChild(overlay);
  document.body.style.overflow = 'hidden';

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
