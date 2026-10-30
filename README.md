# 웹 포즈 검색과 삽화 제작 — Codex 스킬 2종

하나의 웹 검색기와 태그 인덱스를 공유하는 두 스킬입니다.

| 스킬 | 역할 |
|---|---|
| `direct-illustration-poses` · 삽화 포즈 디렉터 | 모호한 장면 설명이나 입력 이미지의 자세를 분석해 웹 레퍼런스를 찾고 실제 이미지를 확인해 반환합니다. 생성하지 않습니다. |
| `create-pose-illustration` · 포즈 참조 삽화 제작 | 검색 스킬로 포즈를 찾고 실제 PNG와 캐릭터 기준 이미지를 참조해 그림을 생성하거나 자세를 편집합니다. |

기본 출처는 [AI Pose Gallery](https://ai-pose-gallery.pages.dev/)입니다. 조건에 맞지 않거나 자료가 없으면 다른 허용된 웹 자료 또는 자세 설명으로 이어갑니다. 이미지와 개인 자료는 이 저장소에 포함하지 않습니다.

## 설치

Python 3.10 이상이 필요합니다. 검색에는 추가 패키지·API 키가 필요하지 않습니다. 생성에는 Codex 환경의 이미지 생성 도구가 필요합니다.

```sh
git clone https://github.com/nothing2that-sys/direct-illustration-poses.git
cd direct-illustration-poses
python install.py
```

현재 사용자의 `~/.agents/skills`에 **두 스킬을 함께** 설치합니다. 기존 동명 스킬이 하나라도 있으면 모두 보존하고 설치를 중단합니다. 업데이트할 때는 기존 두 폴더를 스킬 검색 경로 밖에 백업한 뒤 설치하세요. `--skills-dir <경로>`로 대체 위치를 지정할 수 있습니다. 설치 후 다음 Codex 턴에서 호출할 수 있습니다.

Skill Installer로 설치할 때는 같은 저장소의 `skills/direct-illustration-poses`와 `skills/create-pose-illustration` 두 경로를 함께 지정하세요. 생성 스킬은 검색 스킬에 의존합니다.

## 사용

```text
$direct-illustration-poses 머리가 복잡해서 한 손으로 뺨을 괴는 포즈를 웹에서 찾아줘.
$direct-illustration-poses 이 이미지와 비슷한 자세를 찾아서 후보를 보여줘. 생성은 하지 마.
$create-pose-illustration 이 캐릭터가 기운 없이 축 처진 모습으로 그려줘. 웹 포즈를 찾아 참조해줘.
$create-pose-illustration 이 이미지의 외형과 의상은 유지하고 쪼그려 턱을 괴는 자세로 바꿔줘.
```

입력 이미지는 Codex가 실제로 열어 몸통·팔·손·다리·지지점·인원·시점을 관찰하고 특징 JSON을 작성합니다. 검색 스크립트 자체가 이미지 임베딩 모델인 것은 아닙니다. 캐릭터 외형 참조와 포즈 참조의 역할을 구분합니다.

## 검색 인덱스

기존 태깅의 동의어를 개인정보 없는 [검색 어휘](skills/direct-illustration-poses/assets/query-synonyms.json)로 재사용합니다. [웹 관찰 태그](skills/direct-illustration-poses/assets/verified-web-poses.json)는 실제로 확인한 **웹 이미지 6개 ID**에만 연결했습니다. 원본 번호와 웹 번호의 동일성을 가정하지 않으며, 전체 기존 1,001개 항목의 이미지 일치가 검증된 것은 아닙니다. 다른 앵글에도 관찰 태그를 자동 복사하지 않습니다.

실행 시 웹 텍스트 목록을 읽고 로컬에서 검색합니다. 등록된 관찰 태그가 없는 웹 이미지도 원본 이름·분류와 동의어로 후보를 찾습니다. 검색은 전체 목록을 모델에 전달하지 않고 상위 5개 후보만 출력하며 같은 포즈의 앵글을 묶습니다. `matched`와 `missing`을 구분해 의자 같은 소품이 없는 후보를 정확한 일치로 보고하지 않습니다. 태그를 찾았다는 사실과 실제 이미지를 열어 봤다는 사실도 구분합니다.

```sh
python skills/direct-illustration-poses/scripts/gallery.py search "기운 없이 축 처진" --limit 5
python skills/direct-illustration-poses/scripts/gallery.py search --features pose-features.json
python skills/direct-illustration-poses/scripts/gallery.py show full_single_P012_front
python skills/direct-illustration-poses/scripts/gallery.py fetch full_single_P012_front --kind preview --out work/preview.jpg
# 실제 미리보기를 열어 선택한 뒤 원본 한 장만 받습니다.
python skills/direct-illustration-poses/scripts/gallery.py fetch full_single_P012_front --kind original --out work/pose.png
```

`--line standard/upper/pair/sexy`, `--angle front/high/low/side/diag`, `--exclude`, `--details`를 지원합니다. 기본은 표준 전신 1명입니다. `--cache <경로>`와 `--refresh`는 명령 앞에 지정합니다. [특징 형식과 검색 안내](skills/direct-illustration-poses/references/advanced-search.md)를 참고하세요. 검색 결과는 후보이며 선택한 원본의 자세·손·좌우·접지·소품을 실제로 확인해야 합니다.

## 생성과 이용 범위

생성 스킬은 검색 스킬의 `gallery.py prepare`로 실제 PNG·캐릭터 파일·프롬프트·manifest를 준비한 뒤 사용 가능한 imagegen 스킬과 내장 생성 도구에 전달합니다. “준비까지만”이면 생성하지 않습니다. 생성 도구가 없으면 참조파일과 프롬프트를 반환합니다. 적절한 웹 포즈가 없으면 그 사실과 대안 경로를 명시합니다.

사이트는 작품 제작용 참조와 한 장씩 사용하는 것을 허용하며, 이미지 일괄 다운로드·원본/가공본의 재배포·전재·판매는 금지합니다. 명령을 반복해 전체 이미지를 수집하지 마세요. [원본 사이트](https://ai-pose-gallery.pages.dev/)와 [이용 안내](skills/direct-illustration-poses/references/source-and-terms.md)를 확인하세요. MIT 라이선스는 직접 작성한 코드·문서에 적용되며 외부 이미지의 권리를 부여하지 않습니다.

## 검증

```sh
python -m unittest discover -s tests -v
```

두 스킬 동시 설치와 기존 파일 보존, 모호한 검색·입력 특징·관찰 인덱스 연결·누락 조건·단일 파일 취득·생성 인수의 실제 참조파일을 검사합니다. 사이트 구조와 가용성은 바뀔 수 있으며 검색 일치나 생성 결과의 완전한 재현을 보장하지 않습니다.
