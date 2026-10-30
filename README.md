# 포즈를 찾고, 그 포즈로 그림까지 만드는 Codex 스킬

**설치한 뒤 Codex에 원하는 장면을 말하거나 이미지를 첨부하면 됩니다.**

포즈 자료는 **[AI Pose Gallery](https://ai-pose-gallery.pages.dev/) 안에서만** 찾습니다. 전체 인터넷 검색이나 다른 포즈 사이트로 넘어가지 않습니다.

| 하고 싶은 일 | 사용할 스킬 |
|---|---|
| 포즈 후보와 레퍼런스 이미지만 찾기 | `$direct-illustration-poses` · **삽화 포즈 디렉터** |
| 포즈를 찾아 그림을 만들거나 기존 그림의 자세 바꾸기 | `$create-pose-illustration` · **포즈 참조 삽화 제작** |

두 스킬은 같은 검색기와 태그를 공유합니다. **아래 방법으로 둘 다 설치하세요.**

## 1. 설치하기 — Codex에 이 문장을 붙여 넣으세요

Codex의 새 채팅에 아래 내용을 **통째로 복사해서 보내세요.**

```text
아래 GitHub 저장소의 Codex 스킬 두 개를 현재 사용자용으로 설치해 줘.

https://github.com/nothing2that-sys/direct-illustration-poses

설치할 경로는 저장소 안의 다음 두 개야.
- skills/direct-illustration-poses
- skills/create-pose-illustration

다른 작업 폴더에서도 쓸 수 있도록 실제 사용자 스킬 검색 경로를 확인해서 설치해 줘.
기존 동명 스킬이 있으면 변경 내용을 보존하고, 스킬 검색 경로 밖에 백업한 뒤 업데이트해 줘.
두 스킬이 실제 스킬 목록에 나타나는지 확인해 줘.
앱을 강제 종료하거나 진행 중인 세션을 중단하지 마.
```

설치 과정에서 권한 요청이 나오면 대상 경로와 내용을 확인하세요. 비밀번호나 인증코드를 채팅에 붙여 넣을 필요는 없습니다.

**준비물:** Codex와 Python 3.10 이상. 포즈 검색에는 추가 Python 패키지나 별도 API 키가 필요하지 않습니다. **그림 생성은 해당 Codex 환경에서 이미지 생성 도구를 사용할 수 있어야 합니다.** 도구가 없으면 참조파일과 생성용 프롬프트를 받을 수 있습니다.

### 이미 설치한 사람이 업데이트할 때

위 설치 요청문을 그대로 다시 보내면 됩니다. 기존 파일을 무조건 덮어쓰지 않고 백업하도록 요청한 문장입니다. 직접 설치하는 아래 설치기는 기존 동명 스킬이 있으면 중단합니다.

### 터미널로 직접 설치하고 싶다면

이 부분은 직접 명령을 실행할 사람만 따라 하세요.

```sh
git clone https://github.com/nothing2that-sys/direct-illustration-poses.git
cd direct-illustration-poses
python install.py
```

기본 설치 위치는 현재 사용자의 `~/.agents/skills`이며 **두 스킬을 함께 설치**합니다. 기존 동명 스킬이 하나라도 있으면 덮어쓰지 않고 중단합니다. 업데이트할 때는 기존 두 폴더를 스킬 검색 경로 밖에 백업한 뒤 설치하세요.

Git을 쓰지 않는다면 [현재 버전 ZIP 받기](https://github.com/nothing2that-sys/direct-illustration-poses/archive/refs/heads/main.zip)를 눌러 압축을 풀고, `install.py`가 있는 폴더에서 `python install.py`를 실행하세요. 설치 위치를 직접 정하려면 `python install.py --skills-dir <사용자 스킬 폴더>`를 사용합니다.

## 2. 설치가 됐는지 확인하기

설치가 끝나면 **다음 메시지나 새 채팅**에서 아래 문장을 보내세요.

```text
$direct-illustration-poses
AI Pose Gallery 안에서 “쪼그려 앉아 턱을 괴고 생각하는 옆모습”을 찾아줘.
미리보기와 선택한 원본을 실제로 열어 확인하고, 후보와 출처 링크를 알려줘.
이미지는 생성하지 마.
```

잘 동작하면 갤러리 포즈 후보, 선택 이유와 출처를 받습니다. 현재 확인한 첫 번째 후보는 `full_single_P063_side`입니다. 갤러리 내용이 바뀌면 결과도 달라질 수 있습니다.

스킬이 보이지 않으면 Codex에 **“두 스킬의 사용자 설치 경로와 스킬 목록을 다시 확인해 줘”**라고 요청하세요. 앱 강제 종료부터 할 필요는 없습니다.

## 3. 그대로 복사해서 쓰는 예제

### A. 포즈만 찾기

**이름을 정확히 몰라도 장면을 설명하세요.**

```text
$direct-illustration-poses
머리가 복잡해서 혼자 생각에 잠긴 장면에 어울리는 포즈를 찾아줘.
AI Pose Gallery 내부에서 후보를 골라 실제 이미지를 확인해 줘.
각 후보가 어떤 느낌에 어울리는지 짧게 설명해 줘. 생성은 하지 마.
```

```text
$direct-illustration-poses
기운이 없어서 몸이 축 처진 느낌의 포즈를 찾아줘.
서 있는 자세로, 같은 갤러리 안에서 찾아줘. 생성은 하지 마.
```

### B. 내가 준 이미지와 비슷한 자세 찾기

**먼저 자세를 비교할 이미지를 채팅에 첨부하고** 아래 문장을 보내세요.

```text
$direct-illustration-poses
첨부 이미지와 비슷한 자세의 레퍼런스를 AI Pose Gallery 안에서 찾아줘.
몸통 기울기, 팔과 손 위치, 무릎과 발, 카메라 시점을 중심으로 비교해 줘.
후보 이미지를 실제로 확인하고 비슷한 점과 다른 점을 알려줘.
그림을 새로 만들지는 마.
```

첨부 이미지를 보고 자세 특징으로 검색하는 흐름입니다. 첨부 이미지를 갤러리에 업로드하는 기능은 아닙니다.

### C. 캐릭터 이미지로 새 삽화 만들기

**캐릭터 기준 이미지를 먼저 첨부한 뒤** 보내세요.

```text
$create-pose-illustration
첨부한 캐릭터가 바닥에 앉아 한 손으로 뺨을 괴고 생각하는 삽화를 만들어줘.
얼굴, 머리 모양, 의상과 장비는 첨부 이미지를 유지해 줘.
자세와 구도는 AI Pose Gallery에서 적합한 포즈를 찾아 원본 PNG를 실제로 확인한 뒤 참조해 줘.
캐릭터 외형 참조와 포즈 참조의 역할을 구분해서 그림 한 장을 만들어줘.
```

캐릭터 기준 이미지는 **외형·의상·장비**, 갤러리 포즈 이미지는 **자세·구도**를 담당합니다.

### D. 기존 그림의 자세 바꾸기

**바꾸고 싶은 그림을 먼저 첨부한 뒤** 보내세요.

```text
$create-pose-illustration
첨부 그림의 캐릭터가 쪼그려 앉아 턱을 괴는 옆모습이 되도록 자세를 바꿔줘.
AI Pose Gallery에서 해당 자세를 찾아 실제 원본 이미지를 참조해 줘.
얼굴, 의상, 장비와 그림의 화풍은 유지해 줘.
인물 기준 좌우와 기존 장비 위치도 유지해 줘.
```

### E. 캐릭터 기준 이미지 없이 그림 만들기

외형을 꼭 유지해야 하는 캐릭터가 아니라면 이미지 없이도 요청할 수 있습니다.

```text
$create-pose-illustration
피곤한 성인 여행자가 몸을 앞으로 숙이고 두 손을 무릎에 짚은 그림을 만들어줘.
AI Pose Gallery에서 자세 레퍼런스를 찾아 실제로 확인한 뒤 참조해 줘.
편안한 여행복, 정면 전신, 연필 드로잉 느낌으로 한 명만 그려줘.
```

### F. 생성 전에 참조파일만 준비하기

```text
$create-pose-illustration
한쪽 무릎을 세우고 앉아 뺨을 괴는 장면을 준비해 줘.
AI Pose Gallery에서 포즈를 찾아 미리보기와 원본을 실제로 확인해 줘.
선택한 PNG와 생성용 프롬프트만 준비해 줘.
이번에는 이미지를 생성하지 마.
```

## 4. 검색이 잘 안 될 때

“슬픈 느낌”처럼 추상적인 표현도 사용할 수 있습니다. 결과가 애매하면 **자세 한 가지와 시점 한 가지**를 더 적어 보세요.

| 처음 요청 | 더 구체적인 요청 |
|---|---|
| 고민하는 느낌 | 바닥에 앉아 한 손으로 뺨을 괴는 정면 |
| 지친 느낌 | 상체를 숙이고 두 손을 무릎에 짚은 자세 |
| 편하게 쉬는 느낌 | 옆으로 누워 한 손으로 머리를 받친 자세 |

갤러리에 모든 자세나 소품이 있는 것은 아닙니다. 예를 들어 **의자**를 요청했는데 바닥에 앉은 포즈만 있다면 차이를 알려야 합니다. 맞는 자료가 없다고 다른 사이트에서 가져오지는 않습니다.

생성 요청에서는 적합한 갤러리 이미지를 사용할 수 없을 때 **포즈 이미지 없이 자세 설명으로 진행했다는 사실**을 알리고 이어갈 수 있습니다. 특정 레퍼런스와의 정확한 일치가 꼭 필요하다면 그 한계를 먼저 알립니다.

## 5. 어디까지 테스트했나요?

**검색·설치·참조 준비는 검증했습니다. 최신 버전으로 실제 생성한 그림의 품질까지 검증한 것은 아닙니다.**

| 확인 항목 | 결과 |
|---|---|
| 자동 테스트 | 18개 통과 |
| GitHub 배포 파일과 검증본 대조 | 확인 |
| 두 스킬의 설치·기존 파일 보존 | 확인 |
| 다른 작업 폴더에서 Codex 실제 스킬 목록 조회 | 두 스킬 모두 사용자 스킬로 활성화 확인 |
| 갤러리 내부 한국어 검색·입력 이미지 관찰 특징 검색 | 확인 |
| 선택한 미리보기와 개별 원본 PNG 열람 | 확인 |
| 실제 포즈 파일을 생성 도구용 참조 인수로 준비 | 확인 |
| 갤러리 전용 출처 제한·다른 자료 인덱스 미사용 | 확인 |
| 최신 두 스킬로 새 그림을 생성하고 품질 확인 | **아직 시험하지 않음** |
| 갤러리의 모든 이미지를 한 장씩 전수 확인 | **하지 않음** |

개별 관찰 태그를 붙인 갤러리 이미지는 **6개 ID**입니다. 나머지도 갤러리의 이름·분류와 검색 어휘로 찾지만, 모든 이미지에 상세 관찰 태그가 붙은 것은 아닙니다. 태그가 있어도 최종 후보의 실제 원본을 확인하도록 구성했습니다.

사용자도 처음에는 위 **설치 확인용 검색**으로 한 번 확인한 뒤, 캐릭터 이미지로 생성 예제를 시험하면 됩니다.

## 이용 범위

포즈 출처는 [AI Pose Gallery](https://ai-pose-gallery.pages.dev/)입니다. 제작자와 공식 제휴한 도구는 아닙니다.

사이트는 작품 제작용 참조와 한 장씩 사용하는 것을 허용하며, **이미지 일괄 다운로드·원본 또는 가공본의 재배포·전재·판매는 금지**합니다. 다른 용도 제한도 있으므로 [사이트 안내](https://ai-pose-gallery.pages.dev/)와 [이용 범위](skills/direct-illustration-poses/references/source-and-terms.md)를 확인하세요.

이 저장소에는 갤러리 이미지 자체를 넣지 않습니다. MIT 라이선스는 직접 작성한 코드·문서에 적용되며 외부 이미지의 권리를 부여하지 않습니다.

<details>
<summary>개발자용: 검색 명령과 내부 구조</summary>

검색 스크립트는 Python 표준 라이브러리만 사용합니다.

```sh
python skills/direct-illustration-poses/scripts/gallery.py search "쪼그려서 턱 괴는 옆모습" --limit 5
python skills/direct-illustration-poses/scripts/gallery.py search --features pose-features.json
python skills/direct-illustration-poses/scripts/gallery.py show full_single_P063_side
python -m unittest discover -s tests -v
```

`--line standard/upper/pair/sexy`, `--angle front/high/low/side/diag`, `--exclude`, `--details`를 지원합니다. 기본은 표준 전신 1명입니다. `--cache <경로>`와 `--refresh`는 명령 앞에 지정합니다.

- [입력 이미지의 특징 형식과 검색 안내](skills/direct-illustration-poses/references/advanced-search.md)
- [갤러리 검색 어휘](skills/direct-illustration-poses/assets/query-synonyms.json)
- [직접 확인한 웹 이미지 태그](skills/direct-illustration-poses/assets/verified-web-poses.json)
- [검색 스킬](skills/direct-illustration-poses/SKILL.md)
- [생성 스킬](skills/create-pose-illustration/SKILL.md)

검색은 같은 포즈의 앵글을 묶어 상위 후보만 출력합니다. `matched`와 `missing`은 텍스트·등록 태그의 일치/누락이며 새 이미지 열람의 증거가 아닙니다. 입력 이미지의 특징은 Codex가 실제로 관찰해 작성합니다. 스크립트 자체가 이미지 임베딩 모델은 아닙니다.

사이트 구조·가용성은 변경될 수 있습니다.

</details>
