# Python Thread Parallel

## 프로젝트 개요
해당 프로젝트는 Multi-GPU 리소스를 효율적으로 사용하기 위한 안정적인 큐 시스템을 구축하는 것을 목표로 합니다. RabbitMQ를 활용한 작업 큐 시스템을 통해 분산 처리를 수행하며, Python의 threading을 활용하여 worker 노드에서 병렬로 작업을 처리합니다. 또한, MongoDB를 활용해 작업 결과를 저장하고, Loki 및 Grafana를 통해 로그 모니터링 기능을 제공합니다.

## 구현 내용
- **Python 기반의 분산 큐 시스템**
- **RabbitMQ 클러스터링과 미러링을 활용한 안정적 메시지 큐 시스템 구축**
- **3개의 worker 노드가 메시지를 수신하고 작업을 수행**
- **Python threading을 이용한 멀티스레딩 작업 처리**
- **MongoDB를 활용한 작업 결과 저장**
- **Redis를 활용한 중복 처리 방지**
- **Docker Compose 기반의 컨테이너 실행 환경 제공**
- **Loki, Promtail, Grafana를 통한 로그 모니터링 시스템 구축**
- **테스트 프로그램(tester.py)을 이용한 시뮬레이션 기능 제공**

## 문제점 및 개선
### 1. 작업 중복 처리 문제
- **원인**: 워커 노드의 불안정성으로 인해 작업이 유실되거나 중복 처리될 가능성이 있음.
- **해결 방법**:
  - 워커 노드는 작업 완료 후 `ACK`를 보내고, 실패 시 `nack`를 통해 재시도 처리.
  - RabbitMQ의 메시지 재전송 기능을 활용하여 노드 장애 발생 시 다른 노드에서 작업을 수행.
  - **Redis를 이용하여 작업의 UUID를 캐싱**하여 중복 작업 방지.

### 2. 예외 처리 및 장애 대응
- **각 worker의 thread 마다 예외 처리를 적용**, 하나의 thread에서 오류가 발생해도 시스템 전체에 영향을 주지 않도록 설계.
- **Docker Compose의 `restart: always` 옵션을 사용**하여 노드 장애 발생 시 자동 재시작.
- **Dead Letter Exchange 및 TTL(Time-To-Live) 설정**을 활용하여 유실된 작업을 다른 큐에 저장.
- **RabbitMQ의 클러스터링 및 미러링 기능 활용**, 하나의 노드가 다운되더라도 다른 노드가 대체 가능.

### 3. 모니터링 시스템 구축
- **Loki + Promtail + Grafana를 활용하여 실시간 로그 모니터링**
- **각 노드의 총 처리량 및 처리 시간 분석 가능**
- **Grafana를 통해 worker 노드의 상태를 확인하고 이상 상황을 감지**

### 4. 큐 시스템 안정성 개선
- **Dead Letter Exchange TTL(Time-To-Live)을 활용하여 작업의 유실을 방지하고 지연된 작업을 처리**
- **큐 클러스터링이나 미러링 큐를 이용하여 큐 시스템의 고가용성 확보**

## 프로그램 실행 방법
1. **도커 설치**
2. 다음 명령어 실행:
   ```sh
   git clone https://github.com/Wingseter/python-thread-parallel
   cd python-thread-parallel
   docker compose up --build -d
   ```

## 모니터링 방법
1. **Grafana 접속**
2. `Explore` 클릭
3. `job`을 `workers`로 설정하면 3개의 worker 노드에서 발생한 로그 확인 가능

## 테스트 및 시뮬레이션
### 테스트 프로그램 실행 방법
1. Python 스크립트 실행:
   ```sh
   python tester.py
   ```
2. 옵션을 선택하여 시뮬레이션 수행:
   ```
   📌 테스트할 Worker를 선택하세요:
   1. worker_1 (포트 9001)
   2. worker_2 (포트 9002)
   3. worker_3 (포트 9003)
   ▶ 선택 (1-3): 3
   
   📌 시뮬레이션할 에러 유형을 선택하세요:
   0. 정상 상황: 에러 없이 작업 완료
   1. 에러 상황 1: 작업 중 에러 발생 (ACK 없이 재시도)
   2. 에러 상황 2: 작업 시작 ~ 중간에 Worker 장애 발생 (노드 강제 종료)
   3. 에러 상황 3: 작업 완료 후 노드 불안정 (메시지 중복 가능)
   4. 에러 상황 4: 작업 이후 Worker 장애 발생 (노드 강제 종료)
   ▶ 선택 (0-4): 0
   ```

## 기타 정보
- RabbitMQ 클러스터링을 통해 안정적인 메시지 큐 운영 가능
- MongoDB를 활용하여 작업 결과를 안전하게 저장
- Redis 캐싱을 활용한 중복 작업 방지
- Loki, Promtail, Grafana를 통한 로그 분석 및 실시간 모니터링
- Python threading을 이용한 멀티스레드 기반의 병렬 처리
- Docker Compose를 활용하여 손쉬운 환경 구성 및 배포

이 프로젝트는 대규모 작업을 안정적으로 처리하고 모니터링할 수 있도록 설계되었으며, 향후 확장성을 고려하여 구축되었습니다.

