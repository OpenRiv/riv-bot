import requests
import json
from datetime import datetime, timedelta

def test_recording_api():
    # HTTPS URL
    url = 'https://3.37.89.101:443/recoding/unique'

    # 테스트용 시간 설정
    current_time = datetime.utcnow()
    start_time = current_time - timedelta(minutes=30)

    # 요청 데이터 구성
    payload = {
        "serverUniqueId": 1293863497251291168,
        "channelUniqueId": 1293863497251291171,
        "title": "API 테스트 회의록",
        "text": "이것은 API 테스트를 위한 회의록입니다.",
        "categoryName": "API_TEST",
        "startTime": start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "endTime": current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization':'Bearer '
    }

    # 서버의 자체 서명된 인증서 경로
    ca_cert_path = "bootsecurity.pem"

    try:
        print("\n=== API 요청 정보 ===")
        print(f"URL: {url}")
        print("\n=== 요청 데이터 ===")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

        # HTTPS 요청 시 리다이렉트 방지
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=False,
            allow_redirects=False,  # 리다이렉트 방지
            timeout=30
        )

        print("\n=== 응답 정보 ===")
        print(f"상태 코드: {response.status_code}")
        print(f"응답 헤더: {response.headers}")
        
        # 리다이렉트 대상 URL 출력
        if 'Location' in response.headers:
            print(f"\n🔄 리다이렉트 대상 URL: {response.headers['Location']}")

        print(f"\n응답 내용: {response.text}")

    except requests.exceptions.SSLError as e:
        print(f"\n❌ SSL 오류: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 요청 오류: {str(e)}")

if __name__ == "__main__":
    test_recording_api()
