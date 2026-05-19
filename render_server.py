#!/usr/bin/env python3
"""WorkBuddy Token Stats - 最小化测试版"""

from flask import Flask, jsonify, request
import os
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>WorkBuddy Token Stats</h1><p>API: <a href="/api/stats">/api/stats</a></p>'

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/stats')
def stats():
    try:
        start_str = request.args.get('start', '2026-04-19')
        end_str = request.args.get('end', datetime.now().strftime('%Y-%m-%d'))
        
        start = datetime.strptime(start_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_str, '%Y-%m-%d').date()
        
        # 生成简单的示例数据
        weeks = []
        today = datetime.now().date()
        for i in range(4):
            week_date = today - timedelta(weeks=i)
            monday = week_date - timedelta(days=week_date.weekday())
            sunday = monday + timedelta(days=6)
            
            weeks.append({
                'week': monday.strftime('%Y-W%W'),
                'dateRange': f"{monday.strftime('%m-%d')} ~ {sunday.strftime('%m-%d')}",
                'input': 500000 + (3-i) * 150000,
                'output': 200000 + (3-i) * 80000,
                'cached': int((500000 + (3-i) * 150000) * 0.35),
                'total': 700000 + (3-i) * 230000
            })
        
        total = sum(w['total'] for w in weeks)
        
        return jsonify({
            'period': f'{start_str} ~ {end_str}',
            'weeks': weeks,
            'summary': {
                'total': total,
                'totalInput': sum(w['input'] for w in weeks),
                'totalOutput': sum(w['output'] for w in weeks),
                'totalCached': sum(w['cached'] for w in weeks),
                'cacheRate': 35.0,
                'activeWeeks': len(weeks),
                'dailyAvg': total // 30,
                'days': 30
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
