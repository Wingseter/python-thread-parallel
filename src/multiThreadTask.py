import threading 
from logger import log

# 메시지를 처리하는 테스크 함수 예시로 대문자로 바꾸는 것을 thread로 처리 
def task(message):
    result = [''] * len(message)
    error_flag = threading.Event()

    # 합쳐도 되지만 멀티쓰레드를 표현하기 위해 따로 함수로 분리
    def uppercase_char(char):
        return char.upper()

    def thread_task(char, result, index):
        try:
            result[index] = uppercase_char(char)
        except Exception as e:
            log("error", f"Error in thread_task: {e}")
            error_flag.set()

    # 멀티 쓰레드 배열
    threads = [threading.Thread(target=thread_task, args=(char, result, index)) for index, char in enumerate(message)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # 쓰레드 중 하나라도 에러가 발생하면 에러 처리
    if error_flag.is_set():
        raise Exception("에러상황5: 강화된 멀티 쓰레드 에러 처리")

    uppercased_message = ''.join(result)

    return uppercased_message