import requests
import json
from datetime import datetime, timedelta

def simplify_markdown(text, max_length=1000):
    """
    마크다운 텍스트를 단순화하고 최대 길이를 제한하는 함수.
    - 특수 문자 및 개행을 정제.
    - 최대 길이 초과 시 텍스트 자름.
    """
    simplified_text = (
        text.replace("#", "")  # 헤더 기호 제거
            .replace("-", "")  # 리스트 기호 제거
            .replace("*", "")  # 강조 기호 제거
            .replace("1.", "")  # 번호 리스트 제거
            .replace("2.", "")  # 번호 리스트 제거
            .replace("\n", " ")  # 개행을 공백으로 변환
            .strip()
    )
    # 최대 길이 제한 적용
    if len(simplified_text) > max_length:
        simplified_text = simplified_text[:max_length] + "..."
    return simplified_text

def test_recording_api():
    url = 'https://3.37.89.101:443/recoding/unique'

    # 마크다운 텍스트
    markdown_text = """
## 참석자
- FE 편유나
- BE 편워나

## 회의 내용 요약
백엔드 API 개발은 거의 완료되었고 로그인 기능 연동이 시작될 예정입니다. 프론트엔드는 내일 오전까지 로그인 화면과 상태관리를 마무리할 계획입니다.

## 전체 회의 내용
1. 백엔드 API 진행 상황 논의.
2. 프론트엔드 팀은 로그인 화면과 상태 관리 완료 예정.
3. 에러 핸들링은 로그인 실패 시 401과 403 분리 처리.
4. 프로필조회 API는 금요일까지 제공 예정.
"""

    # 마크다운 단순화 및 길이 제한 적용
    simplified_text = simplify_markdown(markdown_text, max_length=1000)

    # **직접 지정한 startTime과 endTime**
    custom_start_time = "2024-12-18T05:33:43.000000Z"
    custom_end_time = "2024-12-18T05:34:40.000000Z"

    # Payload 구성
    payload = {
        "serverUniqueId": 1318654586638307369,
        "channelUniqueId": 1318654586638307373,
        "title": "API 테스트 회의",
        "text": simplified_text,  # 단순화된 텍스트
        "categoryName": "DEV",
        "startTime": custom_start_time,  # 직접 지정된 시작 시간
        "endTime": custom_end_time       # 직접 지정된 종료 시간
    }

    # 요청 헤더
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'Authorization': 'Bearer YOUR_VALID_TOKEN'  # 여기에 유효한 토큰 입력
    }

    try:
        print("\n=== API 요청 정보 ===")
        print(f"URL: {url}")
        print("\n=== 요청 데이터 ===")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

        # HTTPS 요청
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=False,
            allow_redirects=True,
            timeout=30
        )

        # 응답 결과 출력
        print("\n=== 응답 정보 ===")
        print(f"상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ 요청 오류: {e}")

if __name__ == "__main__":
    test_recording_api()
