import pika, threading

# 타임아웃을 추가한 BlockingConnection
class TimeoutBlockingConnection(pika.BlockingConnection):
    def __init__(self, parameters, timeout=None):
        self.timed_out = False
        # 타임아웃 시 함수
        def timeout_handler():
            self.timed_out = True
            try:
                # 내부 소켓 연결 종료
                if hasattr(self, '_impl'):
                    self._impl._adapter_disconnect()
            except Exception:
                pass

        timer = None
        if timeout:
            timer = threading.Timer(timeout, timeout_handler)
            timer.daemon = True
            timer.start()
        try:
            # 부모 클래스의 BlockingConnection 초기화 
            super().__init__(parameters)
        finally:
            if timer:
                timer.cancel()
        # 타임아웃 되면 예외 발생
        if self.timed_out:
            raise pika.exceptions.AMQPConnectionError("Connection timed out")

