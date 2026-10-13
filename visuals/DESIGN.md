# 시각자료 제작 기록

작성일: 2026-10-13. 교재 범위: 서울·경기 주거용 부동산의 입문 개념.

## 적용한 스킬

[diagram-design](https://github.com/cathrynlavery/diagram-design)의 `skills/diagram-design/SKILL.md`와 스타일·출력·유형·SVG 원칙을 읽었습니다. 참조 커밋은 `0a8ea20ae69b33a5edce6018eedd3a9d26e90c1c`, 스킬 문서의 버전은 `2.6`입니다.

사용 유형은 포함 관계의 Nested, 누적 계산의 Waterfall, 수량 비교의 Bar, 정해진 가상 시점의 Timeline, 조건 분기의 Flowchart입니다. 행동 패턴 목록도 확인했으며 큐·보안 경계·짝지은 정책 평가 등 특정 패턴에는 해당하지 않아 각 유형을 직접 선택했습니다.

## 제작 결정

- 형식: 그림별 독립 HTML + 교재에 넣는 SVG + 8개 그림을 모은 독립 HTML
- 크기: `doc-inline`, SVG `960 × 600`
- 독자: 성인 입문자, 한국어 용어와 짧은 설명
- 색상: 밝은 기본 색상 `paper #f5f5f5`, `ink #2d3142`, `accent #bf4520`
- 글꼴: 시스템 글꼴. 한국어는 Noto Sans KR·Apple SD Gothic Neo·Malgun Gothic 등의 대체 글꼴 사용
- 움직임: 없음. 외부 스크립트·웹폰트·이미지·추적 코드 없음
- 한글과 숫자 표기는 작은 글자를 피하기 위해 대부분 12px 이상, 그룹 제목 14px
- 모바일: 그림 자체를 축소하지 않고 그림 영역 안에서 가로 스크롤
- 인쇄: 가로 스크롤과 최소 폭을 해제해 전체 그림이 페이지에 들어가도록 설정

첫 스타일 선택에 응답이 없어 밝은 기본 색상을 제작 가정으로 사용했습니다. 이름 있는 프로필을 저장하거나 공용 설치의 스타일 가이드를 변경하지 않았습니다. 시스템 글꼴이라 기기별 글자 모양과 폭은 다를 수 있습니다.

## 생략한 범위

한 그림은 한 가지 개념에 집중합니다. 실제 대출 한도·청약 자격·세율·개별 권리 분석·서울 및 경기의 실제 시세와 지역 순위는 그림에 넣지 않았습니다. 임대차 그림에는 권리 요건의 일반 흐름만 담고 예외·배당 순위·보증 절차는 4강으로 연결했습니다. 분양 납부는 대표 3단계만 표시하고 실제 중도금 회차 등은 공고에서 확인하도록 했습니다.

## 데이터와 계산

모든 숫자는 기존 강의의 가상 사례입니다. 전월세 비교만 소수점 한 자리로 반올림했습니다. Waterfall은 `data-role`, `data-value`, `data-name`, `data-carry`로 합계·증감을 선언해 산식과 그림 위치를 대조할 수 있습니다. 막대의 길이는 공통 축으로 계산하고 시간축은 0·6·24개월의 간격을 비례해서 표시했습니다.

## 다시 만들기

소스는 [scripts/build_visuals.py](../scripts/build_visuals.py)입니다. Python 표준 라이브러리만 사용하며 네트워크 호출은 없습니다. SVG 내보내기는 읽은 버전의 Diagram Design `scripts/export_svg.py`에 명시적으로 위임합니다.

```bash
python scripts/build_visuals.py --export-helper /path/to/diagram-design/skills/diagram-design/scripts/export_svg.py
```

명령은 HTML과 SVG를 다시 생성합니다. 그림을 수정하면 연결 강의·양식의 가상 사례와 숫자가 일치하는지 확인합니다.

검증 결과는 [변경 기록](../CHANGELOG.md)에 남깁니다. 실제 측정이나 정책 수치를 추가할 때는 교재의 [출처 관리 원칙](../sources/catalog.md)을 따릅니다.
