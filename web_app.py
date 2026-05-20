from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

DATA_DIR = 'logs'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_log():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        log_file = data.get('file')
        records = data.get('records', [])

        if not log_file or not records:
            return jsonify({'error': 'Missing file or records'}), 400

        file_path = os.path.join(DATA_DIR, log_file)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        return jsonify({'success': True, 'file': log_file, 'count': len(records)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/<path:log_file>')
def get_data(log_file):
    try:
        file_path = os.path.join(DATA_DIR, log_file)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except:
                        pass

        return jsonify(records)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files')
def list_files():
    try:
        files = []
        if os.path.exists(DATA_DIR):
            for root, dirs, filenames in os.walk(DATA_DIR):
                for filename in filenames:
                    if filename.endswith('.log'):
                        rel_path = os.path.relpath(os.path.join(root, filename), DATA_DIR)
                        files.append(rel_path.replace('\\', '/'))

        files.sort(reverse=True)
        return jsonify(files)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest')
def get_latest_data():
    """获取最新的温湿度数据"""
    try:
        all_records = []
        if os.path.exists(DATA_DIR):
            for root, dirs, filenames in os.walk(DATA_DIR):
                for filename in filenames:
                    if filename.endswith('.log'):
                        file_path = os.path.join(root, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            if lines:
                                last_line = lines[-1].strip()
                                if last_line:
                                    try:
                                        record = json.loads(last_line)
                                        all_records.append(record)
                                    except:
                                        pass

        if not all_records:
            return jsonify({'temperature': None, 'humidity': None, 'timestamp': None})

        all_records.sort(key=lambda r: r['timestamp'], reverse=True)
        latest = all_records[0]

        return jsonify({
            'temperature': latest.get('temperature'),
            'humidity': latest.get('humidity'),
            'timestamp': latest.get('timestamp')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/today_trend')
def get_today_trend():
    """获取今日温湿度趋势数据（每5分钟取一个点）"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        all_records = []

        if os.path.exists(DATA_DIR):
            today_dir = os.path.join(DATA_DIR, today)
            if os.path.isdir(today_dir):
                for filename in os.listdir(today_dir):
                    if filename.endswith('.log'):
                        file_path = os.path.join(today_dir, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    try:
                                        record = json.loads(line)
                                        all_records.append(record)
                                    except:
                                        pass

        if not all_records:
            return jsonify({'timestamps': [], 'temperatures': [], 'humidities': []})

        all_records.sort(key=lambda r: r['timestamp'])

        result_timestamps = []
        result_temps = []
        result_hums = []

        if len(all_records) <= 60:
            for r in all_records:
                result_timestamps.append(r['timestamp'])
                result_temps.append(r['temperature'])
                result_hums.append(r['humidity'])
        else:
            step = len(all_records) // 60
            for i in range(0, len(all_records), step):
                r = all_records[i]
                result_timestamps.append(r['timestamp'])
                result_temps.append(r['temperature'])
                result_hums.append(r['humidity'])

        return jsonify({
            'timestamps': result_timestamps,
            'temperatures': result_temps,
            'humidities': result_hums
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/month_kline')
def get_month_kline():
    """获取本月温湿度K线数据（每日最高最低）"""
    try:
        current_month = datetime.now().strftime('%Y-%m')
        daily_data = {}

        if os.path.exists(DATA_DIR):
            for root, dirs, filenames in os.walk(DATA_DIR):
                for dirname in dirs:
                    if dirname.startswith(current_month):
                        date_str = dirname
                        daily_data[date_str] = {'temps': [], 'hums': []}
                        day_dir = os.path.join(root, dirname)
                        for filename in os.listdir(day_dir):
                            if filename.endswith('.log'):
                                file_path = os.path.join(day_dir, filename)
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    for line in f:
                                        line = line.strip()
                                        if line:
                                            try:
                                                record = json.loads(line)
                                                daily_data[date_str]['temps'].append(record['temperature'])
                                                daily_data[date_str]['hums'].append(record['humidity'])
                                            except:
                                                pass

        temp_kline = []
        hum_kline = []

        for date in sorted(daily_data.keys()):
            temps = daily_data[date]['temps']
            hums = daily_data[date]['hums']

            if temps:
                temp_kline.append({
                    'date': date,
                    'high': max(temps),
                    'low': min(temps),
                    'open': temps[0],
                    'close': temps[-1]
                })

            if hums:
                hum_kline.append({
                    'date': date,
                    'high': max(hums),
                    'low': min(hums),
                    'open': hums[0],
                    'close': hums[-1]
                })

        return jsonify({
            'temp_kline': temp_kline,
            'hum_kline': hum_kline
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5002)