/* MANMIN LEGAL REVIEW — Service Worker
   v1.3.8 (2026-11-26) — 하단 단추 통일 — 공통 원본 MM-FAB v1.0 주입(오른쪽 아래 안내 · 초기화 · 앱 설치 · 건물개요 단추를 한 기둥으로 — 단추 72×76 · 건물개요 72×28 · 간격 8px · z-index 1200 · 숨은 단추는 자리 없음 · 설치 뒤 · 앱 실행 중 설치 단추 숨김 · 설치 띠가 뜨면 기둥을 그 위로 · 휴대폰 가로 60×60) · 인쇄 · JPG 에서 앱 설치 안내 띠(.ibar · .iosgd) 숨김(종전 인쇄에 찍힘) — 계산 불변 · MIN 「권장안대로 승인」 · 캐시명 v1.3.8 (종전 v1.3.7)
   v1.3.7 (2026-11-25) — 헤더 고정 — 공통 원본 MM-HEADER v1.1 주입(태블릿 · 데스크톱만 — 폭 768px · 높이 600px 이상, 휴대폰은 고정 없음 · 머리+탭 sticky · 내리면 제목 한 줄+탭으로 접힘 · 다른 sticky 패널 top 보정) — 계산 · 인쇄 불변 · MIN 「추천안대로 승인」 · 「추천안대로 진행해줘」(모바일 제외) · 캐시명 v1.3.7 (종전 v1.3.6)
   범위: /manmin-law/  (메인 사이트 sw.js 와 독립)
   HTML·JSON = 네트워크 우선(매월 갱신 즉시 반영)
   아이콘·정적자원 = 캐시 우선                                */
/* v1.1 — 아이콘 전면 교체(원본 로고 무크롭 재생성). 캐시명을 올려 구 아이콘을 강제 폐기한다. */
/* v1.2 — 첫 화면 「📘 매뉴얼」 단추 · manual/ 신설 · manifest 최신호 자동 갱신 (2026-10-17). */
const CACHE = 'manmin-law-v1.3.8';
const SHELL = [
  './',
  './index.html',
  './manifest.json',
  './assets/logo-full.png',
  './assets/mark-gold.png',
  './assets/mark.png',
  './assets/mark-trans.png',
  './assets/favicon-32.png',
  './assets/apple-touch-icon.png',
  './assets/icon-192.png',
  './assets/icon-512.png',
  './assets/maskable-192.png',
  './assets/maskable-512.png'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(SHELL).catch(() => null))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  const isDoc = req.mode === 'navigate' ||
                url.pathname.endsWith('.html') ||
                url.pathname.endsWith('.json');

  if (isDoc) {
    // 네트워크 우선 — 새 호가 나오면 바로 보이도록
    e.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req).then(r => r || caches.match('./index.html')))
    );
  } else {
    // 캐시 우선 — 아이콘 등 정적자원
    e.respondWith(
      caches.match(req).then(r => r || fetch(req).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
        return res;
      }))
    );
  }
});
