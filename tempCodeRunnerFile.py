        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    try:
        logger.info("회의록 API에 업로드 중...")
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=False,          # SSL 검증 비활성화
            allow_redirects=False, # 리다이렉트 방지
            timeout=30
        )

        logger.info(f"응답 코드: {response.status_code}")
        logger.info(f"응답 내용: {response.text}")
