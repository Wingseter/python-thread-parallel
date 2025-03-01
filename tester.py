import socket

# 미리 정의된 포트 목록 (키 중복 오류 수정)
port_options = {"worker_1": 9001, "worker_2": 9002, "worker_3": 9003}

# 미리 정의된 테스트 목록
test_options = {
    0: "정상 상황: 에러 없이 작업 완료",
    1: "에러 상황 1: 작업 중 에러 발생 (ACK 없이 재시도)",
    2: "에러 상황 2: 작업 시작 ~ 중간에 Worker 장애 발생 (노드 강제 종료)",
    3: "에러 상황 3: 작업 완료 후 노드 불안정 (메시지 중복 가능)",
    4: "에러 상황 4: 작업 이후 Worker 장애 발생 (노드 강제 종료)"
}

def send_error_value(port, value):
    """선택된 포트로 error_num 값을 전송"""
    server_address = ("127.0.0.1", port)
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(server_address)

        client.sendall(str(value).encode("utf-8"))
        response = client.recv(1024).decode("utf-8")
        print(f"[{port}] 서버 응답: {response}")

        client.close()
    except Exception as e:
        print(f"포트 {port}에 연결하는 중 오류 발생: {e}")

if __name__ == "__main__":
    while True:
        print("\n📌 테스트할 Worker를 선택하세요:")
        for idx, worker in enumerate(port_options.keys(), 1):
            print(f"{idx}. {worker} (포트 {port_options[worker]})")
        
        port_choice = input("▶ 선택 (1-3): ").strip()
        if port_choice not in {"1", "2", "3"}:
            print("⚠️ 잘못된 입력입니다! 1, 2, 3 중에서 선택하세요.")
            continue
        
        selected_port = list(port_options.values())[int(port_choice) - 1]

        print("\n📌 시뮬레이션할 에러 유형을 선택하세요:")
        for key, description in test_options.items():
            print(f"{key}. {description}")

        new_value = input("▶ 선택 (0-4): ").strip()
        if new_value not in {"0", "1", "2", "3", "4"}:
            print("⚠️ 잘못된 입력입니다! 0, 1, 2, 3, 4 중에서 선택하세요.")
            continue
        
        new_value = int(new_value)
        send_error_value(selected_port, new_value)
