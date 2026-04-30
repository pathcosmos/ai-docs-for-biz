// mermaid-init.js — MkDocs Material 의 instant navigation 과 호환되는 Mermaid 초기화
// document$ 는 MkDocs Material 이 페이지 전환 시 emit 하는 RxJS Observable
// mermaid.run() API 는 라이브러리 내부에서 안전하게 SVG 를 삽입 (사용자 DOM 조작 불필요)

document$.subscribe(function () {
  if (typeof mermaid === 'undefined') {
    return;
  }

  var theme = document.body.dataset.mdColorScheme === 'slate' ? 'dark' : 'default';

  mermaid.initialize({
    startOnLoad: false,
    theme: theme,
    fontFamily: "'Pretendard', 'Apple SD Gothic Neo', sans-serif",
    flowchart: { useMaxWidth: true, htmlLabels: true, curve: 'basis' },
    sequence: { useMaxWidth: true, mirrorActors: false },
    gantt: { useMaxWidth: true }
  });

  // mermaid.run() 내부에서 안전하게 SVG 삽입 처리
  // querySelector 로 선택된 .mermaid 노드만 변환
  try {
    mermaid.run({ querySelector: '.mermaid' });
  } catch (e) {
    console.warn('[mermaid] run failed:', e);
  }
});
