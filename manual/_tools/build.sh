#!/bin/bash
# 법규 검토 요약 매뉴얼 전체 재생성: 캡처 → WebP → HTML → PDF → 좁은 화면 점검   usage: bash build.sh <repoDir> <rawDir>
set -e; REPO="$(cd "$1" && pwd)"; RAW="$2"; mkdir -p "$RAW"; RAW="$(cd "$RAW" && pwd)"; cd "$(dirname "$0")"; M="$REPO/manual"; mkdir -p "$M/images"
node capture_law.js "$REPO" "$RAW" > "$RAW/_log.json"
python3 - "$RAW" "$M" <<'PY'
import sys,glob,os,shutil
from PIL import Image
raw,M=sys.argv[1],sys.argv[2]
for f in sorted(glob.glob(raw+'/s*.png')):
    Image.open(f).convert('RGB').save(M+'/images/'+os.path.basename(f)[:-4]+'.webp',quality=82,method=6)
shutil.copy(raw+'/_marks.json',M+'/images/_marks.json')
PY
MANUAL_DIR="$M" python3 gen_manual_law.py
node pdf_law.js "$M" 만민법규검토요약_이용매뉴얼_Ver-1.0.pdf "만민 법규 검토 요약 이용 매뉴얼 Ver-1.0"
node audit_responsive.js "$M/index.html" > "$RAW/_audit.json"
