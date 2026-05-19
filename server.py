#!/usr/bin/env python3
"""
WorkBuddy Token Stats 本地服务器
提供实时数据API，自动读取最新的traces数据
"""

from flask import Flask, jsonify, send_from_directory, request
import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

app = Flask(__name__)

def get_week_range(date):
    """获取给定日期所属的自然周范围（周一到周日）"""
    days_since_monday = date.weekday()
    monday = date - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    return monday, sunday

def format_week_number(date):
    """获取周数"""
    monday, _ = get_week_range(date)
    return monday.strftime("%Y-W%W")

def parse_traces(start_date, end_date):
    """解析traces目录获取token使用数据"""
    traces_dir = Path.home() / '.workbuddy' / 'traces'
    if not traces_dir.exists():
        return None
    
    weekly_data = defaultdict(lambda: {'input': 0, 'output': 0, 'cached': 0, 'total': 0})
    
    # 遍历所有traces目录
    for trace_dir in traces_dir.iterdir():
        if not trace_dir.is_dir():
            continue
            
        for trace_file in trace_dir.glob("trace_*.json"):
            try:
                with open(trace_file, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        continue
                    
                    trace = json.loads(content)
                    
                    # 获取trace对象
                    trace_info = trace.get('trace', {})
                    model_info = trace_info.get('modelInfo', {})
                    started_at = trace_info.get('startedAt', '')
                    
                    if not started_at:
                        continue
                    
                    # 解析时间
                    try:
                        trace_date = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                        trace_date_local = trace_date.replace(tzinfo=None)
                    except (ValueError, AttributeError):
                        continue
                    
                    # 检查日期范围
                    if not (start_date <= trace_date_local.date() <= end_date):
                        continue
                    
                    # 获取周信息
                    week_key = format_week_number(trace_date_local)
                    
                    # 获取token数据
                    input_tokens = model_info.get('totalInputTokens', 0) or 0
                    output_tokens = model_info.get('totalOutputTokens', 0) or 0
                    cached_tokens = model_info.get('totalCachedTokens', 0) or 0
                    
                    weekly_data[week_key]['input'] += input_tokens
                    weekly_data[week_key]['output'] += output_tokens
                    weekly_data[week_key]['cached'] += cached_tokens
                    weekly_data[week_key]['total'] += input_tokens + output_tokens
                    
            except (json.JSONDecodeError, IOError):
                continue
    
    # 格式化输出
    result = []
    for week_key in sorted(weekly_data.keys()):
        # 获取该周的日期范围
        try:
            year = int(week_key[:4])
            week_num = int(week_key.split("-W")[1])
            # 计算周一的日期
            first_day = datetime.strptime(f"{year}-1-1", "%Y-%m-%d")
            monday = first_day - timedelta(days=first_day.weekday()) + timedelta(weeks=week_num - 1)
            sunday = monday + timedelta(days=6)
            date_range = f"{monday.strftime('%m-%d')} ~ {sunday.strftime('%m-%d')}"
        except:
            date_range = ""
            
        data = weekly_data[week_key]
        result.append({
            'week': week_key,
            'dateRange': date_range,
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
    start_date_str = request.args.get('start', '2026-04-19')
    end_date_str = request.args.get('end', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    data = parse_traces(start_date, end_date)
    
    if data is None:
        return jsonify({'error': 'Traces directory not found'}), 404
    
    # 计算汇总
    total_input = sum(d['input'] for d in data)
    total_output = sum(d['output'] for d in data)
    total_cached = sum(d['cached'] for d in data)
    total_all = sum(d['total'] for d in data)
    
    # 计算缓存率 (cached / (input + output))
    effective_total = total_input + total_output
    cache_rate = (total_cached / effective_total * 100) if effective_total > 0 else 0
    
    # 计算天数
    days = (end_date - start_date).days + 1
    
    return jsonify({
        'period': f"{start_date_str} ~ {end_date_str}",
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
