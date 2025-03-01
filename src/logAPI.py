from flask import Flask, jsonify, request
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
LOKI_URL = "http://loki:3100/loki/api/v1/query_range"

@app.route('/logs', methods=['GET'])
def get_logs():
    # 최근 1시간 동안의 로그를 가져오기
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    params = {
        "query": '{}',  # 모든 로그 가져오기
        "limit": 50,  # 최근 50개 로그 가져오기
        "direction": "backward",
        "start": int(start_time.timestamp() * 1e9),  # 나노초 단위 변환
        "end": int(end_time.timestamp() * 1e9)
    }

    response = requests.get(LOKI_URL, params=params)
    
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        return jsonify({"error": "Failed to decode JSON response from Loki"}), 500

    logs = []
    for stream in data.get("data", {}).get("result", []):
        for value in stream.get("values", []):
            timestamp, message = value
            logs.append({"timestamp": timestamp, "message": message})

    return jsonify(logs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
