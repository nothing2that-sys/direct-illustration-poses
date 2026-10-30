# 삽화 포즈 디렉터

[AI Pose Gallery / POSE-DB-01](https://ai-pose-gallery.pages.dev/)에서 장면에 맞는 포즈를 찾고 캐릭터 참조와 연결하는 Codex 스킬입니다. 갤러리 조건이 맞지 않으면 다른 허용된 자료나 자세 설명으로 계속 진행합니다.

한국어 장면 검색, 일본어 키워드 확장, 표준 전신·상반신·2인 분류, 5개 앵글 필터를 지원합니다. 검색은 텍스트 메타데이터만 읽습니다. 선택한 이미지 한 장을 가져오고, 로컬 참조파일과 생성용 프롬프트를 준비할 수 있습니다. 생성 도구가 있으면 실제 파일을 전달하며, 준비 명령 자체는 이미지를 생성하지 않습니다.

## 설치

Python 3.10 이상과 Codex가 필요합니다. 추가 Python 패키지나 API 키, 개인 Drive 연결은 필요하지 않습니다.

```sh
git clone https://github.com/nothing2that-sys/direct-illustration-poses.git
cd direct-illustration-poses
python install.py
```

현재 사용자의 `~/.agents/skills/direct-illustration-poses`에 설치됩니다. 기존 동명 스킬이 있으면 보존하고 중단합니다. 다른 위치가 필요하면 `python install.py --skills-dir <사용자-스킬-폴더>`를 사용하세요. 설치 후 다음 Codex 턴에서 호출하세요. 표시가 늦으면 스킬 목록을 새로고침하세요.

Codex의 Skill Installer에 다음과 같이 요청해도 됩니다.

```text
https://github.com/nothing2that-sys/direct-illustration-poses 의
skills/direct-illustration-poses 스킬을 설치해 줘.
현재 사용자 스킬 검색 경로를 확인하고 기존 동명 스킬은 덮어쓰지 마.
```

## 사용

```text
$direct-illustration-poses 앉아서 고민하는 장면의 포즈를 찾아 줘.
미리보기와 선택한 원본을 실제로 확인하고 참조파일까지만 준비해 줘.
새 삽화는 생성하지 마.
```

스크립트를 직접 실행할 수도 있습니다. 설치된 스킬의 `scripts/gallery.py` 또는 이 저장소의 경로를 사용하세요.

```sh
python skills/direct-illustration-poses/scripts/gallery.py search "앉아서 고민" --line standard --angle front
python skills/direct-illustration-poses/scripts/gallery.py show full_single_P012_front
python skills/direct-illustration-poses/scripts/gallery.py fetch full_single_P012_front --kind preview --out work/preview.jpg
# 미리보기를 실제로 열어 선택한 뒤 원본 한 장만 가져옵니다.
python skills/direct-illustration-poses/scripts/gallery.py fetch full_single_P012_front --kind original --out work/pose.png
# 원본과 캐릭터 이미지를 실제로 열어 확인합니다.
python skills/direct-illustration-poses/scripts/gallery.py prepare --pose-file work/pose.png --pose-id full_single_P012_front --scene "앉아서 고민하는 인물" --out references-output/example
```

`--character <이미지>`를 추가하면 캐릭터 자료도 복사합니다. 캐릭터는 외형·의상·장비, 포즈는 자세·구도를 담당합니다. `--constraints`에 인물 기준 좌우·소품·시점 제약을 적으세요. 미리보기와 원본은 모두 실제로 열어 확인해야 합니다. 검색 결과가 의자 등 특정 소품을 보장하지 않으며, 일치하지 않는 조건은 명시해야 합니다.

메타데이터 캐시는 `~/.cache/direct-illustration-poses/gallery.json`에 저장됩니다. `--cache <경로>`로 바꾸거나 명령 앞에 `--refresh`를 붙여 갱신할 수 있습니다. 실제 이미지와 준비 결과는 지정한 로컬 작업 폴더에만 저장됩니다. 출력에 로컬 절대 경로가 포함되므로 공개 커밋하지 마세요.

## 갤러리 없이 계속 진행하기 (v1.1.0)

갤러리 출처의 이용 제한을 생성 도구 전체의 제한으로 취급하지 않습니다. 예를 들어 역사적 인물의 청동 동상을 나무 자세로 편집할 때 갤러리 이용 조건이 맞지 않으면, 해당 용도를 허용하는 별도 포즈 이미지나 일반적인 나무 자세 설명을 사용합니다. 편집 대상인 동상 사진은 외형·갑옷·청동 질감을 위한 실제 참조로 전달합니다. 포즈 이미지가 없는 경로에서는 그 사실을 명시하고 가짜 포즈 참조를 만들지 않습니다.

```text
$direct-illustration-poses 이 동상 사진의 외형과 청동 질감을 유지해
요가 나무 자세로 바꿔 줘. 갤러리 조건이 맞지 않으면 다른 허용된
포즈 자료나 자세 설명으로 진행하고, 실제 사용한 참조를 알려 줘.
```

허용된 외부 포즈를 사용하려면 이미지를 확인한 뒤 준비 명령에 `--pose-source external --source-url <원본페이지> --rights-note "<확인한 허락·용도>"`를 추가하세요. 사용자 제공 로컬/Drive 이미지는 `--pose-source user`로 표시합니다. 갤러리 외부 자료는 PNG·JPEG·WebP를 지원합니다.

이미지 없이 자세 설명으로 준비할 수도 있습니다. 아래 명령은 인터넷에 접속하거나 포즈 이미지를 다운로드하지 않습니다.

```sh
python skills/direct-illustration-poses/scripts/gallery.py prepare --pose-description "한 다리로 서고 반대 발을 지지 다리의 종아리에 댄다. 무릎 관절은 피하고 두 손을 가슴 앞에 모은다. 정면 전신 구도." --fallback-reason "갤러리 이용 조건과 맞지 않아 자세 설명으로 진행" --scene "청동 동상의 나무 자세" --character work/statue.png --constraints "동상의 얼굴·투구·갑옷·청동 질감과 기존 장비 위치 유지" --out references-output/tree-pose
```

결과 manifest는 `reference_mode`로 gallery_image / external_image / user_image / description_only를 구분합니다. 설명 경로의 생성 인수에는 편집 대상만 포함되고 포즈 파일·갤러리 ID는 없습니다. 생성 요청이 이미 있으면 입력 이미지를 실제로 확인한 뒤 생성 도구로 이어갑니다. 참조 준비만 요청한 경우에는 생성하지 않습니다. 출처 조건을 숨기거나 생성 도구 자체의 거절을 우회하지 않습니다.

## 이미지 이용 조건

사이트는 작품 제작용 참조·편집·상업 이용과 한 장씩 참조하는 이용을 허용한다고 안내합니다. **이미지 일괄 다운로드, 이미지 원본·가공본의 재배포·전재·판매는 금지**합니다. 명령을 반복해 전체 자료를 수집하지 마세요. 최신 조건은 [원본 사이트](https://ai-pose-gallery.pages.dev/)와 [이용 범위](skills/direct-illustration-poses/references/source-and-terms.md)를 확인하세요.

이 저장소에는 사이트 이미지·썸네일·목록 덤프가 없습니다. 코드와 직접 작성한 문서만 MIT 라이선스로 배포합니다. 외부 이미지의 권리를 새로 부여하지 않습니다. 사이트와 공식 제휴 관계가 없는 독립적인 참조 보조 도구입니다.

## 검증과 한계

```sh
python -m unittest discover -s tests -v
```

한국어 검색 확장, HTML 목록 파싱, 외부 이미지 URL 거부, 검색 시 이미지 요청 없음, 단일 파일 취득, 기존 파일 보존, 참조 준비를 검사합니다. 사이트 구조·가용성은 변경될 수 있습니다. 파싱 실패 시 자동 우회하지 않고 브라우저에서 선택·다운로드하거나 직접 받은 파일을 사용합니다. 이미지 생성 모델·브라우저 도구는 별도 환경에서 제공되어야 합니다.
