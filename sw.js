/* MANMIN LEGAL REVIEW — Service Worker
   범위: /KIMMANMIN/law/  (메인 사이트 sw.js 와 독립)
   HTML·JSON = 네트워크 우선(매월 갱신 즉시 반영)
   아이콘·정적자원 = 캐시 우선                                */
/* v1.1 — 아이콘 전면 교체(원본 로고 무크롭 재생성). 캐시명을 올려 구 아이콘을 강제 폐기한다. */
const CACHE = 'manmin-law-v1.1';
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
