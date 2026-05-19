#!/usr/bin/env python3
"""本地数据服务 - 提供真实的 traces 数据供云端页面使用"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

app = Flask(__name__)
CORS(app)  # 允许跨域访问

DEFAULT_TRACES_DIR = Path.home() / '.workbuddy' / 'traces'

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'defaultPath': str(DEFAULT_TRACES_DIR)})

@app.route('/api/stats')
def stats():
    try:
        start_str = request.args.get('start', datetime.now().strftime('%Y-%m-01'))
        end_str = request.args.get('end', datetime.now().strftime('%Y-%m-%d'))
        traces_path = request.args.get('path', str(DEFAULT_TRACES_DIR))
        
        start = datetime.strptime(start_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_str, '%Y-%m-%d').date()
        TRACES_DIR = Path(traces_path)
        
        # 读取真实 traces 数据
        week_data = {}
        trace_count = 0
        
        if TRACES_DIR.exists():
            for session_dir in TRACES_DIR.iterdir():
                if session_dir.is_dir():
                    for trace_file in session_dir.glob('trace_*.json'):
                        try:
                            with open(trace_file, 'r') as f:
                                data = json.load(f)
                            trace = data.get('trace', {})
                            started_at = trace.get('startedAt', '')
                            if started_at:
                                trace_date = datetime.fromisoformat(started_at.replace('Z', '+00:00')).date()
                                if start <= trace_date <= end:
                                    trace_count += 1
                                    # 计算所在周
                                    monday = trace_date - timedelta(days=trace_date.weekday())
                                    sunday = monday + timedelta(days=6)
                                    week_key = monday.strftime('%Y-%m-%d')
                                    
                                    if week_key not in week_data:
                                        week_data[week_key] = {
                                            'week': monday.strftime('%Y-W%W'),
                                            'dateRange': f"{monday.strftime('%m-%d')} ~ {sunday.strftime('%m-%d')}",
                                            'input': 0,
                                            'output': 0,
                                            'cached': 0,
                                            'total': 0
                                        }
                                    
                                    model_info = trace.get('modelInfo', {})
                                    input_tok = model_info.get('totalInputTokens', 0) or 0
                                    output_tok = model_info.get('totalOutputTokens', 0) or 0
                                    cached_tok = model_info.get('totalCachedTokens', 0) or 0
                                    
                                    week_data[week_key]['input'] += input_tok
                                    week_data[week_key]['output'] += output_tok
                                    week_data[week_key]['cached'] += cached_tok
                                    week_data[week_key]['total'] += input_tok + output_tok
                        except Exception:
                            continue
        
        weeks = sorted(week_data.values(), key=lambda w: w['week'])
        
        total = sum(w['total'] for w in weeks)
        total_input = sum(w['input'] for w in weeks)
        total_output = sum(w['output'] for w in weeks)
        total_cached = sum(w['cached'] for w in weeks)
        cache_rate = (total_cached / max(total_input + total_output, 1) * 100)
        
        return jsonify({
            'period': f'{start_str} ~ {end_str}',
            'weeks': weeks,
            'summary': {
                'total': total,
                'totalInput': total_input,
                'totalOutput': total_output,
                'totalCached': total_cached,
                'cacheRate': round(cache_rate, 1),
                'activeWeeks': len(weeks),
                'dailyAvg': total // max((end - start).days + 1, 1),
                'days': (end - start).days + 1,
                'traceCount': trace_count
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("📡 本地数据服务已启动...")
    print("📍 访问地址: http://localhost:8081")
    print("📂 默认数据路径:", DEFAULT_TRACES_DIR)
    print("📝 打开云端页面，点击「刷新数据」按钮即可获取真实数据")
    print("   可在页面顶部设置自定义数据路径")
    print("按 Ctrl+C 停止服务")
    app.run(host='127.0.0.1', port=8081)
