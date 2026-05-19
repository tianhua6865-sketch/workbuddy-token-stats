#!/usr/bin/env python3
"""
WorkBuddy Token Stats 本地服务器
提供实时数据API，自动读取最新的traces数据
"""

from flask import Flask, jsonify, send_from_directory
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

def get_week_range(year, week):
    """获取自然周的日期范围"""
    jan4 = datetime(year, 1, 4)
    week_start = jan4 + timedelta(weeks=week-1, days=-jan4.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start.strftime('%m-%d'), week_end.strftime('%m-%d')

def parse_traces(start_date, end_date):
    """解析traces目录获取token使用数据"""
    traces_dir = Path.home() / '.workbuddy' / 'traces'
    if not traces_dir.exists():
        return None
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    weekly_data = defaultdict(lambda: {'input': 0, 'output': 0, 'cached': 0, 'total': 0})
    
    for trace_file in traces_dir.rglob('*.json'):
        try:
            with open(trace_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    
                    # 获取trace对象（数据在 trace 字段内）
                    trace = data.get('trace', {})
                    
                    started_at = trace.get('startedAt', '')
                    if not started_at:
                        continue
                    
                    # 解析时间
                    try:
                        dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                        dt_local = dt.astimezone()
                    except (ValueError, AttributeError):
                        continue
                    
                    # 检查日期范围
                    if not (start.date() <= dt_local.date() <= end.date()):
                        continue
                    
                    # 获取周信息
                    year, week_num, _ = dt_local.isocalendar()
                    week_key = f"{year}-W{week_num:02d}"
                    
                    # 获取token数据
                    input_tokens = trace.get('totalInputTokens', 0) or 0
                    output_tokens = trace.get('totalOutputTokens', 0) or 0
                    cached_tokens = trace.get('totalCachedTokens', 0) or 0
                    total_tokens = trace.get('totalTokens', 0) or 0
                    
                    # 如果totalTokens为0，从其他字段计算
                    if total_tokens == 0:
                        total_tokens = input_tokens + output_tokens
                    
                    weekly_data[week_key]['input'] += input_tokens
                    weekly_data[week_key]['output'] += output_tokens
                    weekly_data[week_key]['cached'] += cached_tokens
                    weekly_data[week_key]['total'] += total_tokens
                    
        except (json.JSONDecodeError, KeyError, ValueError, IOError) as e:
            continue
    
    # 格式化输出
    result = []
    for week_key in sorted(weekly_data.keys()):
        year = int(week_key[:4])
        week_num = int(week_key[6:])
        date_range = get_week_range(year, week_num)
        data = weekly_data[week_key]
        result.append({
            'week': week_key,
            'dateRange': f"{date_range[0]} ~ {date_range[1]}",
            'input': data['input'],
            'output': data['output'],
            'cached': data['cached'],
            'total': data['total']
        })
    
    return result

@app.route('/')
def index():
    return send_from_directory('.', 'token-stats.html')

@app.route('/api/stats')
def get_stats():
    start_date = request.args.get('start', '2026-04-19')
    end_date = request.args.get('end', datetime.now().strftime('%Y-%m-%d'))
    
    data = parse_traces(start_date, end_date)
    
    if data is None:
        return jsonify({'error': 'Traces directory not found'}), 404
    
    # 计算汇总
    total_input = sum(d['input'] for d in data)
    total_output = sum(d['output'] for d in data)
    total_cached = sum(d['cached'] for d in data)
    total_all = sum(d['total'] for d in data)
    
    # 计算缓存率
    cache_rate = (total_cached / total_all * 100) if total_all > 0 else 0
    
    # 计算天数
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    days = (end - start).days + 1
    
    return jsonify({
        'period': f"{start_date} ~ {end_date}",
        'weeks': data,
        'summary': {
            'totalInput': total_input,
            'totalOutput': total_output,
            'totalCached': total_cached,
            'total': total_all,
            'cacheRate': round(cache_rate, 1),
            'activeWeeks': len(data),
            'dailyAvg': total_all // days if days > 0 else 0,
            'days': days
        }
    })

if __name__ == '__main__':
    from flask import request
    print("=" * 50)
    print("  🚀 WorkBuddy Token Stats Server")
    print("=" * 50)
    print()
    print("  📊 访问页面: http://localhost:8080")
    print("  📅 默认统计: 过去30天")
    print("  🔗 API: http://localhost:8080/api/stats")
    print()
    print("  按 Ctrl+C 停止服务器")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=False)
