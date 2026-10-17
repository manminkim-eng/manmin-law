# -*- coding: utf-8 -*-
"""만민 법규 검토 요약(MANMIN LEGAL REVIEW) 이용 매뉴얼 생성기 — MANMIN 매뉴얼 공통 엔진 사용
   실행: MANUAL_DIR=<manual 폴더> python gen_manual_law.py  →  <manual>/index.html
   수치(호수 · 건수 · 단계별 건수 · 마감일)는 저장소 data/*.json 에서 직접 읽는다 — 손으로 옮겨 적지 않는다.
   캡처 기준일 = CAP_DATE (D-day 표시는 캡처한 날 기준으로 칠해진다)."""
import os, sys, json, glob
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manual_engine import fig, T, render, B, MARKS

VER, DATE, CAP_DATE = 'Ver-1.0', '2026-10-17', '2026-10-17'
PDF = '만민법규검토요약_이용매뉴얼_Ver-1.0.pdf'
SITE = 'https://manminkim-eng.github.io/manmin-law/'
APP = '만민 법규 검토 요약'
REPO = os.path.abspath(os.path.join(B, '..'))
ISSUES = sorted((json.load(open(f, encoding='utf-8')) for f in glob.glob(os.path.join(REPO, 'data', '20??-??.json'))), key=lambda d: d['issue'], reverse=True)
LATEST = ISSUES[0]
ORDER = ['시행법령', '훈령예규고시', '국회통과', '입법예고', '행정예고', '의원발의', '추가검토']
def cnt(d):
    c = {}
    for it in d['items']: c[it['cat']] = c.get(it['cat'], 0) + 1
    return c
LC = cnt(LATEST)
TOTAL = sum(len(d['items']) for d in ISSUES)
assert LATEST['issue'] == '2026-09' and len(LATEST['items']) == 46 and LC == {'시행법령': 10, '훈령예규고시': 1, '국회통과': 2, '입법예고': 8, '행정예고': 2, '의원발의': 21, '추가검토': 2}, LC
assert TOTAL == 177 and len(ISSUES) == 5, TOTAL
IT = {f'i{i:02d}': x for i, x in enumerate(LATEST['items'], 1)}
OPEN = [(k, x) for k, x in IT.items() if x.get('deadline') and x['deadline'] >= CAP_DATE]
OPEN.sort(key=lambda kx: kx[1]['deadline'])
def dd(s): return (date.fromisoformat(s) - date.fromisoformat(CAP_DATE)).days
def dot(s): return s.replace('-', '.') + '.'
def F(sid, cap, legend=None, **kw):
    if legend is None:
        legend = [k['label'] for k in MARKS.get(sid, {}).get('marks', [])] or None
    return fig(sid, cap, legend, **kw)
K = lambda t: '<div class="k1">' + t + '</div>'
CC = {"시행법령": "#d4a843", "국회통과": "#e0645c", "훈령예규고시": "#b98ce0", "입법예고": "#4ea8de", "행정예고": "#6fc08a", "의원발의": "#f0a05a", "추가검토": "#8b98b3"}
TAG = lambda c: f'<span class="ctag" style="--c:{CC[c]}">{c}</span>'
EXTRA_CSS = """<style>
.ctag{display:inline-block;font-size:12px;font-weight:700;padding:1px 9px;border-radius:6px;border:1px solid var(--c);color:#1A1A2E;background:color-mix(in srgb,var(--c) 22%,#fff);white-space:nowrap}
#fig-s02_chips{max-width:900px}#fig-s10_text{max-width:720px}#fig-s12_print{max-width:520px}
#fig-s07_card,#fig-s08_notice,#fig-s03_watch,#fig-s04_archive{max-width:900px}
.k1 td:first-child,.k1 th:first-child{white-space:nowrap}
.flow{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:16px 0}
.flow div{border-radius:10px;padding:12px 10px;background:#fff;border:1px solid var(--line);border-top:4px solid var(--c);font-size:14px;line-height:1.5}
.flow b{display:block;color:var(--navy-d);font-size:15px;margin-bottom:2px}
.flow i{font-style:normal;font-size:12px;color:var(--text2)}
.cal{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:14px 0}
.cal div{background:var(--navy-l);border-radius:10px;padding:14px 16px}
.cal div.next{background:var(--accent-l);border:1px solid var(--accent)}
.cal b{display:block;font-size:18px;color:var(--navy-d)}
.cal span{font-size:13px;color:var(--text2)}
@media (max-width:1024px){.flow{grid-template-columns:repeat(3,1fr)}}
@media (max-width:640px){.flow{grid-template-columns:repeat(2,1fr)}.cal{grid-template-columns:1fr}}
@media print{
  figure.shot{max-width:none!important}
  figure.shot .frame{width:fit-content;max-width:100%}
  figure.shot img{width:auto;height:auto;max-width:100%;max-height:118mm}
  #fig-s12_print img,#fig-s13_mobile_index img,#fig-s14_mobile_card img{max-height:150mm}
  .pair{grid-template-columns:1fr 1fr}.flow{grid-template-columns:repeat(3,1fr)}
}
</style>"""

TOC = [
 ('ch0', '0. 이 매뉴얼에 대하여', []),
 ('ch1', '1. 월간 발간 안내', [('s1-1', '발간일 · 수록 기간'), ('s1-2', '발간 일정'), ('s1-3', '함께 보는 매체')]),
 ('ch2', '2. 수록 기준', [('s2-1', '6단계 수집'), ('s2-2', '분야 · 대상 법령'), ('s2-3', '확인 방법')]),
 ('ch3', '3. 화면 안내', [('s3-1', '첫 화면'), ('s3-2', '지금 챙겨야 할 일정'), ('s3-3', '월별 아카이브'), ('s3-4', '월호 머리'), ('s3-5', '검색 · 필터 · 도구'), ('s3-6', '항목 카드'), ('s3-7', '예고 항목과 D-day'), ('s3-8', '블로그 · 유튜브 원고'), ('s3-9', '인쇄 · 밝은 화면'), ('s3-10', '휴대전화 · 앱 설치')]),
 ('ch4', '4. 항목 읽는 법', [('s4-1', '카드 구성'), ('s4-2', '날짜 표기'), ('s4-3', 'D-day 규칙')]),
 ('ch5', '5. 2026년 9월호 살펴보기', [('s5-1', '머리기사'), ('s5-2', '단계별 건수'), ('s5-3', '의견 제출 가능한 예고')]),
 ('ch6', '6. 실무 활용', [('s6-1', '매월 확인 순서'), ('s6-2', '자주 묻는 질문')]),
 ('ch7', '부록', [('a1', '발간 이력'), ('a2', '발간 절차 (편집)'), ('a3', '용어'), ('a4', '매뉴얼 변경 내역')]),
]
S_ = []
S_.append(f"""{EXTRA_CSS}<section class="ch" id="ch0"><h2><span class="n">00</span>이 매뉴얼에 대하여</h2>
<p class="lead">{APP}(MANMIN LEGAL REVIEW)은 건축사 김만민이 <b>매월 첫째 화요일</b>에 <b>직전 달</b>의 건축 · 구조 · 기계설비 · 소방 · 토목 관련 법령 개정사항을 정리해 발간하는 <b>정기 월간 웹 간행물</b>입니다. 이 매뉴얼은 간행물의 발간 체계와 수록 기준, 화면 사용법, 항목을 읽고 실무에 쓰는 방법을 설명합니다.</p>
{K(T([
 ['간행물', f'{APP} · <b>MANMIN VER-1.0</b> · 월간 (매월 첫째 화요일)'],
 ['접속 주소', f'<a href="{SITE}" target="_blank" rel="noopener">manminkim-eng.github.io/manmin-law</a>'],
 ['최신호', f'<b>{LATEST["label"]}호</b> · 발간 {LATEST["published"]} · {len(LATEST["items"])}건'],
 ['누적', f'{len(ISSUES)}개호 · {TOTAL}건 (2026년 5월호 ~ {LATEST["label"]}호)'],
 ['매뉴얼 판', f'<b>{VER}</b> (초판) · {DATE} · 작성 김만민 건축사(㈜대성건축사사무소)'],
 ['내려받기', f'<a href="{PDF}" download>PDF(A4)</a> · <a href="../index.html">간행물 열기</a>'],
 ['화면 캡처 기준', f'{CAP_DATE} — 화면의 D-day · 「종료」 표시는 보는 날짜에 따라 달라집니다'],
], ['항목', '내용']))}
<div class="note"><b>성격</b>법령 원문을 대신하지 않습니다. 각 항목은 법제처 국가법령정보센터 · 국민참여입법센터 · 국회 의안 원문으로 바로 연결되며, 인허가 · 감리 판단은 반드시 원문과 부칙의 시행일로 확인합니다.</div>
</section>""")

cal = ''.join(f'<div class="{"next" if n else ""}"><span>{a}</span><b>{b}</b><span>{c}</span></div>' for a, b, c, n in [
 ('2026-09-01(화) 발간', '2026년 8월호', '08-01 ~ 08-31 수록', 0),
 ('2026-10-06(화) 발간', '2026년 9월호', '09-01 ~ 09-30 수록 · 최신호', 0),
 ('2026-11-03(화) 발간 예정', '2026년 10월호', '10-01 ~ 10-31 수록 · 다음 호', 1)])
S_.append(f"""<section class="ch" id="ch1"><h2><span class="n">01</span>월간 발간 안내</h2>
<p class="lead">한 달 동안 나온 법령 변화를 그달이 끝난 뒤 한 번에 정리합니다. 달이 끝나야 그달의 공포 · 예고 · 발의가 모두 확정되기 때문입니다.</p>
<h3 id="s1-1">발간일 · 수록 기간</h3>
{K(T([
 ['발간일', '<b>매월 첫째 화요일</b>'],
 ['수록 기간', '<b>직전 달 1일 ~ 말일</b> (예: 11월 첫째 화요일 → 10월호)'],
 ['발간 단위', '월호(YYYY-MM) — 예: 2026-09 = 2026년 9월호'],
 ['수정', '발간 뒤 누락이 확인되면 다음 호 「추가검토」로 보완 수록합니다 (예: 9월호에 7월 누락분 1건)'],
], ['항목', '내용']))}
<h3 id="s1-2">발간 일정</h3>
<div class="cal">{cal}</div>
<h3 id="s1-3">함께 보는 매체</h3>
{T([
 ['웹 간행물', f'<a href="{SITE}" target="_blank" rel="noopener">manminkim-eng.github.io/manmin-law</a>', '원본 — 원문 연결 · D-day · 검색 · 인쇄'],
 ['네이버 블로그', '<a href="https://blog.naver.com/manmin72" target="_blank" rel="noopener">blog.naver.com/manmin72</a>', '월호 원고 (웹의 「블로그 원고」로 추출)'],
 ['유튜브', '<a href="https://www.youtube.com/@김만민-x8p" target="_blank" rel="noopener">@김만민-x8p</a>', '월호 해설 영상 · 쇼츠'],
 ['MANMIN 계산도구', '<a href="https://manminkim-eng.github.io/KIMMANMIN/" target="_blank" rel="noopener">manminkim-eng.github.io/KIMMANMIN</a>', '같은 분야의 엔지니어링 웹 계산도구 모음'],
], ['매체', '주소', '역할'])}
</section>""")

flow = ''.join(f'<div style="--c:{CC[c]}"><b>{n}</b>{c}<br><i>{s}</i></div>' for n, c, s in [
 ('①', '입법예고', '국민참여입법센터'), ('②', '행정예고', '국민참여입법센터'), ('③', '의원발의', '열린국회정보'),
 ('④', '국회통과', '열린국회정보'), ('⑤', '시행법령', '국가법령정보센터'), ('⑥', '훈령예규고시', '국가법령정보센터')])
S_.append(f"""<section class="ch" id="ch2"><h2><span class="n">02</span>수록 기준</h2>
<p class="lead">법령이 만들어지는 길목을 6단계로 나누어 매달 모두 훑습니다. <b>한 단계라도 수집이 빠지면 그 호는 발간하지 않습니다.</b> 해당 단계에 실적이 없으면 「0건」으로 기록합니다.</p>
<h3 id="s2-1">6단계 수집</h3>
<div class="flow">{flow}</div>
{T([
 [TAG('시행법령'), '법률 · 시행령 · 시행규칙의 공포 · 시행 확정분', '국가법령정보센터 (부칙 대조)', '이미 정해졌다 — 시행일부터 적용'],
 [TAG('훈령예규고시'), '고시 · 훈령 · 예규 발령분', '국가법령정보센터 행정규칙', '운영기준 · 세부기준이 바뀐다'],
 [TAG('국회통과'), '본회의 의결 법률안', '열린국회정보', '곧 공포된다 — 다음 호 「시행법령」 후보'],
 [TAG('입법예고'), '정부 법령안 입법예고', '국민참여입법센터', '아직 안 · 마감 전 의견 제출 가능'],
 [TAG('행정예고'), '고시 · 지침 행정예고', '국민참여입법센터', '아직 안 · 마감 전 의견 제출 가능'],
 [TAG('의원발의'), '국회의원 발의 법률안', '열린국회정보', '방향 참고 — 확정이 아니다'],
 [TAG('추가검토'), '지난 호 누락분 · 관련 정책 묶음', '위 출처 동일', '보완 수록'],
], ['단계', '대상', '출처', '실무 의미'])}
<div class="tip"><b>읽는 순서</b>확정(시행법령 · 훈령예규고시) → 임박(국회통과 · 마감 전 예고) → 방향(의원발의) 순으로 보면 이번 달 업무에 바로 쓰이는 것부터 챙길 수 있습니다.</div>
<h3 id="s2-2">분야 · 대상 법령</h3>
<p>각 항목에는 분야 태그가 붙습니다 — 건축 · 구조 · 기계설비 · 소방 · 토목 · 전기 · 도시계획 · 안전진단 · 환경. 수집 대상은 실무 관련 <b>법령명 53개</b>를 명시한 목록(화이트리스트)으로 정하고, 이름이 비슷해 잘못 걸리는 법령 15개는 제외 목록으로 끊습니다(예: 「전기통신」 · 「기초연금」 · 「도로교통법」). 농지법은 설계 · 감리 실무 대상이 아니어서 의도적으로 수집하지 않습니다(2026-09-01 결정).</p>
{T([
 ['시행법령 감시목록', '36건', '매월 공포 · 시행 여부를 법령명으로 개별 조회 · 부칙 대조 (전수 스캔 아님)'],
 ['훈령 · 예규 · 고시 감시목록', '14건', '매월 발령 여부를 명칭으로 개별 조회 (전수 스캔 아님)'],
 ['법령명 화이트리스트', '53개', '예고 · 발의 자동 수집 대상'],
 ['제외 목록', '15개 + 농지법', '오탐 차단 · 범위 밖'],
], ['목록', '규모', '쓰임'], num_cols=(1,))}
<h3 id="s2-3">확인 방법</h3>
<ul>
<li>공포 · 시행 확정분은 법령 번호와 공포일 · 시행일을 <b>국가법령정보센터 연혁 · 부칙</b>과 대조합니다. 같은 날 여러 개정이 겹치면 현행 화면에는 나중 시행분만 보이므로 연혁으로 확인합니다(예: 9월호 국토계획법 시행령 대통령령 제36656호 — 9.18. 시행 타법개정 제36587호가 현행 머리에 표시됨).</li>
<li>「제안이유 및 주요내용」은 정부 · 발의자가 밝힌 공식 사유를 그대로 옮깁니다. 편집자의 해석은 「실무 영향」에만 씁니다.</li>
<li>발간 전 자동 점검(<code>publish.py check</code>)이 제안이유가 빈 항목, 수집 실패 단계, 발간일 규칙 위반을 찾아 발간을 막습니다.</li>
</ul>
</section>""")

S_.append(f"""<section class="ch" id="ch3"><h2><span class="n">03</span>화면 안내</h2>
<p class="lead">첫 화면(index)은 지금 챙겨야 할 일정과 월별 아카이브를, 월호 페이지(YYYY-MM)는 그달의 전체 항목을 보여 줍니다.</p>
<h3 id="s3-1">첫 화면</h3>
{F('s01_index', '첫 화면 — 머리 막대 · 소개 · 바로가기 단추')}
{F('s02_chips', '바로가기 단추 — 유튜브 오른쪽에 「📘 매뉴얼」')}
{T([
 ['최신호 보기', '가장 최근 월호로 이동'],
 ['링크 공유', '공유 기능이 있는 기기(휴대전화 등)는 공유 창, 없으면 주소 복사'],
 ['네이버 블로그 · 유튜브', '같은 내용의 블로그 원고 · 해설 영상 채널'],
 ['📘 매뉴얼', '이 매뉴얼 (새 창)'],
 ['월별 아카이브 이동', '머리 막대 목록에서 원하는 호로 바로 이동'],
 ['웹에 추가 · ◐', '앱으로 설치 · 밝게/어둡게 전환'],
], ['단추', '기능'])}
<h3 id="s3-2">지금 챙겨야 할 일정</h3>
{F('s03_watch', '예고 마감 · 시행 예정 — 모든 호에서 발간(빌드) 날 이후 날짜를 골라 가까운 순으로 최대 8건')}
<p>모든 호의 입법예고 · 행정예고 마감일과 앞으로 시행될 항목을 모아 가까운 날짜부터 보여 줍니다. 목록은 발간 때 정해지고, D-day 표시만 보는 날 기준으로 다시 계산됩니다. 제목을 누르면 해당 월호로, 「원문 ↗」은 입법예고 원문으로 갑니다.</p>
<h3 id="s3-3">월별 아카이브</h3>
{F('s04_archive', '월별 아카이브 — 호 번호 · 머리기사 · 건수 · 발간일')}
<h3 id="s3-4">월호 머리</h3>
{F('s05_issue_hero', '월호 머리 — 호 번호 · 머리기사 · 발간일 · 수집 출처 · 단계별 건수')}
<h3 id="s3-5">검색 · 필터 · 도구</h3>
{F('s06_toolbar', '도구 막대 — 검색 · 단계 · 분야 필터 · 펼치기 · 인쇄 · 공유 · 원고')}
{T([
 ['검색', '법령명 · 조문 · 키워드 (단축키 <kbd>/</kbd>)'],
 ['단계 필터', '시행법령 · 국회통과 · 훈령예규고시 · 입법예고 · 행정예고 · 의원발의 · 추가검토'],
 ['분야 필터', '건축 · 구조 · 기계설비 · 소방 · 토목 등 — 단계 필터와 함께 걸림'],
 ['전체 펼치기', '모든 카드의 「세부 개정내용」을 한 번에 펼침 · 접기'],
 ['인쇄 · PDF 저장', '브라우저 인쇄 — 「PDF로 저장」 선택'],
 ['블로그 · 유튜브 원고', '현재 필터에 보이는 항목만 원고로 추출'],
], ['도구', '기능'])}
{F('s09_filter', '분야 필터 예 — 「소방」만 표시, 오른쪽 표시 건수가 바뀜')}
<h3 id="s3-6">항목 카드</h3>
{F('s07_card', '항목 카드 — 주택법 공포(법률 제21902호) · 세부 개정내용을 펼친 상태')}
<h3 id="s3-7">예고 항목과 D-day</h3>
{F('s08_notice', '입법예고 항목 — 마감이 지나면 「입법예고 종료」로 표시')}
<h3 id="s3-8">블로그 · 유튜브 원고</h3>
{F('s10_text', '원고 추출 창 — 네이버 블로그용 · 유튜브 대본용 전환 · 전체 복사')}
<p>보이는 항목만 추출되므로, 예를 들어 「소방」 필터를 건 뒤 원고를 열면 소방 항목만으로 원고가 만들어집니다.</p>
<h3 id="s3-9">인쇄 · 밝은 화면</h3>
<div class="pair"><div>{F('s12_print', '인쇄 화면 — A4 · 흰 바탕')}</div><div>{F('s11_light', '밝은 화면(◐) — 첫 화면')}</div></div>
<h3 id="s3-10">휴대전화 · 앱 설치</h3>
<div class="pair"><div>{F('s13_mobile_index', '휴대전화 첫 화면 (390 px)', narrow=True)}</div><div>{F('s14_mobile_card', '휴대전화 항목 카드', narrow=True)}</div></div>
<p>「웹에 추가」를 누르면 주소창 없는 독립 창으로 설치됩니다(PWA). 설치한 앱의 바로가기 「최신호 보기」는 매월 발간 때 최신호로 자동 갱신됩니다(v1.2).</p>
</section>""")

ex = IT['i03']
S_.append(f"""<section class="ch" id="ch4"><h2><span class="n">04</span>항목 읽는 법</h2>
<h3 id="s4-1">카드 구성</h3>
{T([
 ['단계 · 분야 태그', '어느 단계의 무엇인가', f'{TAG("시행법령")} · 건축'],
 ['제목', '핵심 변경을 한 줄로', ex['title']],
 ['날짜 · 근거', '공포 / 시행 / 예고기간 · 근거 법령 · 원문', f'{ex["dateLabel"]} {ex["date"]} · {ex["law"]}'],
 ['요약', '법령 번호 · 공포일 · 시행일 · 주요 수치', '법률 제21902호(2026.9.8. 공포)'],
 ['제안이유 및 주요내용', '정부 · 발의자의 공식 사유 (원문 그대로)', '—'],
 ['세부 개정내용', '조문별 시행일 · 부칙 경과조치', f'{len(ex["detail"])}건'],
 ['신 · 구조문 대비', '법제처 원문 · 법령 검색 연결', '—'],
 ['실무 영향', '설계 · 인허가 · 감리에서 달라지는 점 (편집자 의견)', ex['impact'][:60] + '…'],
 ['링크', '항목 주소 복사 — 동료에게 그 항목만 공유', '#i03'],
], ['구성', '담는 내용', '9월호 i03 예'])}
<h3 id="s4-2">날짜 표기</h3>
{T([
 ['시행', '그날부터 적용', '시행법령'],
 ['공포', '공포만 되고 시행일은 따로 — 요약 · 세부에서 시행일 확인', '시행법령'],
 ['발령', '고시 · 훈령 · 예규 발령일', '훈령예규고시'],
 ['의결', '국회 본회의 의결일', '국회통과'],
 ['예고기간', '예고 시작일 · 마감일', '입법예고 · 행정예고'],
 ['발의', '법률안 발의일', '의원발의'],
], ['표기', '뜻', '쓰는 단계'])}
<div class="warn"><b>주의</b>「공포」 항목은 시행일이 다를 수 있습니다. 같은 법률 안에서도 조문마다 시행일이 갈리는 경우가 많으므로(예: 공공주택 특별법 — 공포일 시행 · 일부 조문 2027.3.9. 시행) 「세부 개정내용」의 부칙 내용을 확인합니다.</div>
<h3 id="s4-3">D-day 규칙</h3>
{T([
 ['예고 마감 11일 이상', '「입법예고 마감 D-n」 회색', '여유 있음'],
 ['예고 마감 10일 이내', '「입법예고 마감 D-n」 강조', '의견 제출 준비'],
 ['마감 당일', '「마감 D-DAY」', '당일 제출'],
 ['마감 지남', '「입법예고 종료」', '다음 단계(공포) 대기'],
 ['시행 예정', '「시행 D-n」 녹색', '시행 전 준비'],
], ['상태', '표시', '실무'])}
<p>D-day는 페이지를 여는 날짜로 계산합니다. 같은 9월호라도 10월 초에 보면 「마감 D-9」, 마감 뒤에 보면 「종료」로 보입니다.</p>
</section>""")

heads = [IT[k] for k in ('i08', 'i03', 'i02', 'i05', 'i06')]
rows_open = [[TAG(x['cat']), x['title'], f'{x["deadline"]}', f'D-{dd(x["deadline"])}'] for k, x in OPEN]
S_.append(f"""<section class="ch" id="ch5"><h2><span class="n">05</span>2026년 9월호 살펴보기</h2>
<p class="lead">{LATEST['label']}호는 {LATEST['published']}(화)에 발간됐고 {len(LATEST['items'])}건을 수록했습니다. 머리기사 — {LATEST['headline']}</p>
<h3 id="s5-1">머리기사</h3>
{T([[TAG(x['cat']), x['title'], f'{x["dateLabel"]} {x["date"]}'] for x in heads], ['단계', '항목', '날짜'])}
<h3 id="s5-2">단계별 건수</h3>
{T([[TAG(c), LC.get(c, 0), {'시행법령':'공포 · 시행 확정','훈령예규고시':'고시 발령','국회통과':'본회의 의결','입법예고':'정부안 예고','행정예고':'고시안 예고','의원발의':'법률안 발의','추가검토':'7월 누락분 · 정책 묶음'}[c]] for c in ORDER] + [['<b>합계</b>', f'<b>{len(LATEST["items"])}</b>', '']], ['단계', '건수', '내용'], num_cols=(1,))}
<h3 id="s5-3">의견 제출 가능한 예고 ({CAP_DATE} 기준)</h3>
{T(rows_open, ['단계', '항목', '마감', '남은 날'], num_cols=(3,))}
<div class="tip"><b>활용</b>마감 전 예고는 국민참여입법센터 원문(카드의 「입법예고 원문 ↗」)에서 의견을 낼 수 있습니다. 소방시설법 시행령(공장 스프링클러) · 건축법 시행령(다세대 · 다가구 바닥면적)처럼 설계 기준이 바뀌는 예고는 진행 중인 계획안에 미리 반영 여부를 검토합니다.</div>
</section>""")

S_.append(f"""<section class="ch" id="ch6"><h2><span class="n">06</span>실무 활용</h2>
<h3 id="s6-1">매월 확인 순서</h3>
<ol class="steps">
<li><b class="t">첫째 화요일 — 최신호 열기</b>첫 화면 「최신호 보기」 또는 설치한 앱의 「최신호」 바로가기.</li>
<li><b class="t">확정분 먼저</b>단계 필터 「시행법령」 · 「훈령예규고시」 → 진행 중인 설계 · 인허가 · 감리 현장에 걸리는지 확인. 시행일과 경과조치(부칙)는 원문으로 대조.</li>
<li><b class="t">내 분야만</b>분야 필터(건축 · 소방 · 기계설비 …)로 좁혀 놓고 「전체 펼치기」.</li>
<li><b class="t">임박 일정</b>첫 화면 「지금 챙겨야 할 일정」에서 예고 마감 · 시행 예정 확인 → 필요하면 의견 제출.</li>
<li><b class="t">공유 · 보관</b>항목 「링크」로 동료에게 해당 항목만 공유, 「인쇄 · PDF 저장」으로 현장 서류에 첨부.</li>
</ol>
<h3 id="s6-2">자주 묻는 질문</h3>
{T([
 ['발간일에 열었는데 지난달 호가 최신호입니다', '발간은 첫째 화요일 중에 반영됩니다. 앱 화면이 예전 내용이면 새로 고침하거나 앱을 다시 엽니다(HTML은 네트워크 우선으로 받습니다).'],
 ['항목 날짜와 법제처 현행 화면의 번호가 다릅니다', '같은 날 · 같은 달에 개정이 겹치면 현행 화면 머리에는 나중 시행분이 보입니다. 국가법령정보센터 「연혁」에서 해당 번호를 찾습니다(2장 확인 방법).'],
 ['의원발의 항목도 지켜야 하나요', '아니요. 의원발의는 국회 심사 전 단계로 확정이 아닙니다. 방향 참고용이며, 통과되면 「국회통과」 → 「시행법령」으로 다시 실립니다.'],
 ['예고가 「종료」로 바뀌었습니다', '의견 제출 기간이 끝났다는 뜻입니다. 공포되면 이후 호 「시행법령」에 실립니다.'],
 ['지난 호를 보려면', '첫 화면 「월별 아카이브」 또는 머리 막대의 호 선택 목록.'],
 ['블로그 원고에 일부 항목만 넣고 싶습니다', '단계 · 분야 필터나 검색으로 원하는 항목만 남긴 뒤 원고를 엽니다.'],
], ['질문', '답'])}
</section>""")

hist = [[d['label'] + '호', d['published'], len(d['items']), ' · '.join(f'{c} {cnt(d)[c]}' for c in ORDER if c in cnt(d))] for d in ISSUES]
S_.append(f"""<section class="ch" id="ch7"><h2><span class="n">부록</span>발간 이력 · 절차 · 용어</h2>
<h3 id="a1">발간 이력</h3>
{T(hist + [['<b>누적</b>', '', f'<b>{TOTAL}</b>', f'{len(ISSUES)}개호']], ['호', '발간일', '건수', '단계별'], num_cols=(2,))}
<p>2025-09 · 2025-10 · 2025-12 · 2026-01 네 개 호(협회 법규교육 자료 기반)는 수집 기준이 달라 사이트에 싣지 않고 보관만 합니다.</p>
<h3 id="a2">발간 절차 (편집)</h3>
{T([
 ['① 수집', '<code>python publish.py collect</code>', '입법예고 · 행정예고 · 의원발의 · 국회통과 자동 수집 → 초안'],
 ['② 작성', '사람', '실을 항목 선택 · 요약 · 제안이유 · 실무 영향 작성 · 공포 · 시행 확정분은 법령정보로 대조해 추가'],
 ['③ 점검', '<code>python publish.py check</code>', '빈 제안이유 · 수집 실패 단계 · 발간일 규칙 위반이면 발간 차단'],
 ['④ 발간', '<code>python publish.py release --push</code>', '점검 → 빌드(첫 화면 · 월호 · 앱 바로가기 갱신) → 커밋 → 게시'],
], ['단계', '명령', '내용'])}
<h3 id="a3">용어</h3>
{T([
 ['공포', '법령을 관보에 게재해 알리는 것 — 시행과 다를 수 있음'],
 ['시행', '법령의 효력이 실제로 생기는 날'],
 ['부칙', '시행일 · 경과조치 · 적용례를 정한 조항'],
 ['입법예고', '정부가 법령안을 미리 알리고 의견을 받는 절차'],
 ['행정예고', '고시 · 지침 등 행정규칙안을 미리 알리는 절차'],
 ['타법개정', '다른 법령의 제정 · 개정에 따라 함께 바뀌는 개정'],
 ['PWA', '웹을 앱처럼 설치해 쓰는 방식 — 「웹에 추가」'],
], ['용어', '뜻'])}
<h3 id="a4">매뉴얼 변경 내역</h3>
{T([[VER, DATE, '초판 — 첫 화면 「📘 매뉴얼」 단추 신설과 함께 발행 (사이트 서비스워커 v1.2)']], ['판', '날짜', '내용'])}
</section>""")

html = render(title=f'{APP} 이용 매뉴얼 {VER}', desc='매월 첫째 화요일 발간하는 건축 · 구조 · 기계설비 · 소방 · 토목 법령 개정 요약 — 발간 체계 · 수록 기준 · 화면 사용법 · 실무 활용',
              eyebrow='MANMIN LEGAL REVIEW · MONTHLY · USER MANUAL', h1=f'{APP} 이용 매뉴얼', sub='매월 첫째 화요일, 지난달 법령 변화를 6단계로 — 발간 체계 · 수록 기준 · 화면 사용법 · 실무 활용',
              ver=VER, date=DATE, app_name='간행물', pdf=PDF, toc=TOC, sections=S_, foot_note='법령 원문을 대신하지 않습니다 — 원문 · 부칙으로 확인')
html = html.replace('<span class="rev">· 화면 대응 개정 2026-10-12</span>', '')
out = os.path.join(B, 'index.html')
open(out, 'w', encoding='utf-8', newline='\n').write(html)
print('ok', out, len(html), 'open-notices', len(OPEN))
