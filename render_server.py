#!/usr/bin/env python3
"""WorkBuddy Token Stats - 真实数据版"""

from flask import Flask, jsonify, request
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

app = Flask(__name__)

TRACES_DIR = Path.home() / '.workbuddy' / 'traces'

HTML_PAGE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WorkBuddy Token 使用量统计</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f8fafc;color:#1e293b;padding:20px}
.container{max-width:1200px;margin:0 auto}
header{text-align:center;margin-bottom:30px}
header h1{font-size:2rem;color:#6366f1;margin-bottom:8px}
header p{color:#64748b}
.card{background:#fff;border-radius:16px;padding:24px;margin-bottom:24px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}
.card-title{font-size:1.1rem;font-weight:600;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.card-title::before{content:'';width:4px;height:20px;background:#6366f1;border-radius:2px}
.date-picker{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:16px}
.date-input{display:flex;align-items:center;gap:8px}
.date-input label{font-weight:500;color:#64748b;font-size:0.9rem}
.date-input input{padding:8px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:0.95rem}
.btn{padding:10px 20px;background:#6366f1;color:white;border:none;border-radius:8px;font-size:1rem;cursor:pointer}
.btn:hover{background:#818cf8}
.btn:disabled{opacity:0.6;cursor:not-allowed}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:24px}
.stat-card{background:linear-gradient(135deg,#6366f1,#818cf8);color:white;padding:20px;border-radius:12px}
.stat-card.success{background:linear-gradient(135deg,#10b981,#34d399)}
.stat-card.warning{background:linear-gradient(135deg,#f59e0b,#fbbf24)}
.stat-label{font-size:0.85rem;opacity:0.9;margin-bottom:4px}
.stat-value{font-size:1.6rem;font-weight:700}
.stat-sub{font-size:0.75rem;opacity:0.8;margin-top:4px}
table{width:100%;border-collapse:collapse;font-size:0.9rem}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid #e2e8f0}
th{background:#f8fafc;font-weight:600;color:#64748b;font-size:0.8rem}
tr:hover{background:#f8fafc}
.week-tag{background:#6366f1;color:white;padding:2px 10px;border-radius:12px;font-size:0.85rem}
.total-row{background:#f8fafc;font-weight:600}
.num{font-family:monospace;font-size:0.9rem}
.chart-container{position:relative;height:300px;margin:20px 0}
.tips{background:linear-gradient(135deg,#fef3c7,#fde68a);border-radius:12px;padding:20px}
.tips h4{color:#92400e;margin-bottom:12px}
.tips ul{list-style:none}
.tips li{padding:6px 0;padding-left:24px;position:relative;color:#78350f;font-size:0.9rem}
.tips li::before{content:'💡';position:absolute;left:0}
.loading{text-align:center;padding:40px;color:#64748b}
.error{background:#fee2e2;color:#991b1b;padding:20px;border-radius:12px;text-align:center}
.last-update{text-align:right;font-size:0.8rem;color:#64748b;margin-top:8px}
.status-indicator{display:inline-flex;align-items:center;gap:6px;font-size:0.9rem}
.status-dot{width:8px;height:8px;border-radius:50%;background:#10b981;animation:pulse 2s infinite}
.status-dot.offline{background:#ef4444;animation:none}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
</style>
</head>
<body>
<div class="container">
<header><h1>📊 WorkBuddy Token 使用量统计</h1><span class="status-indicator"><span class="status-dot" id="statusDot"></span><span id="statusText">检测中...</span></span></header>

<div class="card">
<div class="card-title">📂 数据源</div>
<div style="margin-top:12px">
<label style="font-size:0.9rem;color:#64748b">日期范围：</label>
<div class="date-input" style="display:inline-flex;margin-left:8px"><input type="date" id="startDate" value="{{START_DATE}}"></div>
<span style="margin:0 8px;color:#64748b">至</span>
<div class="date-input" style="display:inline-flex"><input type="date" id="endDate" value="{{END_DATE}}"></div>
<button class="btn" id="refreshBtn" onclick="loadData()" style="margin-left:16px">🔄 刷新数据</button>
</div>
<!-- 上传区域（默认隐藏，本地服务离线时显示） -->
<div id="uploadArea" style="display:none;margin-top:16px;padding:20px;background:#f0fdf4;border-radius:12px">
<p style="color:#166534;font-size:0.9rem;margin:0 0 12px 0">📤 请上传 traces JSON 文件：</p>
<div style="display:flex;gap:12px;flex-wrap:wrap">
<input type="file" id="fileUpload" accept=".json" multiple style="display:none" onchange="handleFileUpload(this)">
<button class="btn" onclick="document.getElementById('fileUpload').click()" style="background:#16a34a">📁 选择文件</button>
<button class="btn" onclick="showUploadHint()" style="background:#6366f1">❓ 格式说明</button>
</div>
<p id="uploadStatus" style="margin-top:12px;font-size:0.85rem;color:#166534"></p>
</div>
<div class="last-update" id="lastUpdate"></div>
</div>

<div class="stats-grid">
<div class="stat-card"><div class="stat-label">总使用量</div><div class="stat-value" id="totalTokens">--</div><div class="stat-sub">Tokens</div></div>
<div class="stat-card success"><div class="stat-label">缓存复用率</div><div class="stat-value" id="cacheRate">--</div><div class="stat-sub">节省成本</div></div>
<div class="stat-card warning"><div class="stat-label">活跃周数</div><div class="stat-value" id="activeWeeks">--</div><div class="stat-sub">周</div></div>
<div class="stat-card"><div class="stat-label">日均使用</div><div class="stat-value" id="dailyAvg">--</div><div class="stat-sub">Tokens/天</div></div>
</div>

<div class="card"><div class="card-title">📈 每周使用量趋势</div><div class="chart-container"><canvas id="trendChart"></canvas></div></div>
<div class="card"><div class="card-title">📋 详细统计表</div><div id="tableContainer"><div class="loading">正在加载数据...</div></div></div>
<div class="card"><div class="card-title">💡 分析结果与优化建议</div><div id="analysisContent"><div class="loading">正在分析...</div></div></div>
</div>

<script>
let chart = null;
let uploadedData = null; // 保存上传的文件数据

function fmt(n) {
    return (n || 0).toLocaleString();
}

function setStatus(online) {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    if (online) {
        dot.classList.remove('offline');
        text.textContent = '本地服务在线';
    } else {
        dot.classList.add('offline');
        text.textContent = '本地服务离线';
    }
}

function showUploadHint() {
    alert('数据格式说明：\n\n请上传 WorkBuddy traces 目录下的 JSON 文件。\n\n每个文件应包含 trace 数据，格式如下：\n\n{\n  "trace": {\n    "startedAt": "2026-05-19T08:00:00.000Z",\n    "modelInfo": {\n      "totalInputTokens": 100000,\n      "totalOutputTokens": 5000,\n      "totalCachedTokens": 80000\n    }\n  }\n}\n\n可以从 ~/.workbuddy/traces/ 目录复制文件上传。');
}

function handleFileUpload(input) {
    const files = input.files;
    if (!files || files.length === 0) return;
    
    const status = document.getElementById('uploadStatus');
    status.textContent = '正在读取文件...';
    
    let processed = 0;
    let totalInput = 0, totalOutput = 0, totalCached = 0;
    let traceCount = 0;
    const start = document.getElementById('startDate').value;
    const end = document.getElementById('endDate').value;
    const startDate = new Date(start);
    const endDate = new Date(end);
    
    // 按周分组
    const weekData = {};
    
    for (const file of files) {
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const data = JSON.parse(e.target.result);
                const trace = data.trace || {};
                const startedAt = trace.startedAt;
                
                if (startedAt) {
                    const traceDate = new Date(startedAt);
                    if (traceDate >= startDate && traceDate <= endDate) {
                        traceCount++;
                        const modelInfo = trace.modelInfo || {};
                        const input = modelInfo.totalInputTokens || 0;
                        const output = modelInfo.totalOutputTokens || 0;
                        const cached = modelInfo.totalCachedTokens || 0;
                        
                        totalInput += input;
                        totalOutput += output;
                        totalCached += cached;
                        
                        // 计算周
                        const day = traceDate.getDay();
                        const monday = new Date(traceDate);
                        monday.setDate(traceDate.getDate() - (day === 0 ? 6 : day - 1));
                        const sunday = new Date(monday);
                        sunday.setDate(monday.getDate() + 6);
                        
                        const weekKey = monday.toISOString().split('T')[0];
                        if (!weekData[weekKey]) {
                            weekData[weekKey] = {
                                week: (monday.getFullYear()) + '-W' + getWeekNumber(monday),
                                dateRange: formatMD(monday) + ' ~ ' + formatMD(sunday),
                                input: 0, output: 0, cached: 0, total: 0
                            };
                        }
                        weekData[weekKey].input += input;
                        weekData[weekKey].output += output;
                        weekData[weekKey].cached += cached;
                        weekData[weekKey].total += input + output;
                    }
                }
            } catch (err) {
                console.error('Parse error:', file.name, err);
            }
            
            processed++;
            status.textContent = `已处理 ${processed}/${files.length} 个文件...`;
            
            if (processed === files.length) {
                const weeks = Object.values(weekData).sort((a, b) => a.week.localeCompare(b.week));
                const total = totalInput + totalOutput;
                const cacheRate = total > 0 ? (totalCached / (totalInput + totalOutput) * 100) : 0;
                
                uploadedData = {
                    period: start + ' ~ ' + end,
                    weeks: weeks,
                    summary: {
                        total: total,
                        totalInput: totalInput,
                        totalOutput: totalOutput,
                        totalCached: totalCached,
                        cacheRate: Math.round(cacheRate * 10) / 10,
                        activeWeeks: weeks.length,
                        dailyAvg: Math.round(total / Math.max((endDate - startDate) / 86400000 + 1, 1)),
                        days: Math.round((endDate - startDate) / 86400000 + 1),
                        traceCount: traceCount
                    }
                };
                
                document.getElementById('uploadStatus').textContent = '✅ 已读取 ' + traceCount + ' 条记录，共 ' + traceCount + ' 个文件';
                renderData(uploadedData, '上传文件');
            }
        };
        reader.readAsText(file);
    }
}

function getWeekNumber(date) {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}

function formatMD(date) {
    return (date.getMonth() + 1).toString().padStart(2, '0') + '-' + date.getDate().toString().padStart(2, '0');
}

function renderData(d, source) {
    document.getElementById('totalTokens').textContent = fmt(d.summary.total);
    document.getElementById('cacheRate').textContent = (d.summary.cacheRate || 0) + '%';
    document.getElementById('activeWeeks').textContent = d.summary.activeWeeks || 0;
    document.getElementById('dailyAvg').textContent = fmt(d.summary.dailyAvg);
    document.getElementById('lastUpdate').textContent = '最后更新: ' + new Date().toLocaleTimeString() + ' (' + source + ')';
    
    updateChart(d.weeks || []);
    updateTable(d.weeks || [], d.summary);
    generateAnalysis(d);
}

async function loadData() {
    const s = document.getElementById('startDate').value;
    const e = document.getElementById('endDate').value;
    if (!s || !e) {
        alert('请选择日期范围');
        return;
    }
    
    const btn = document.getElementById('refreshBtn');
    btn.disabled = true;
    btn.textContent = '⏳ 加载中...';
    
    // 尝试从本地服务拉取
    try {
        const url = 'http://localhost:8081/api/stats?start=' + s + '&end=' + e;
        const r = await fetch(url, { timeout: 2000 });
        if (r.ok) {
            const d = await r.json();
            renderData(d, '本地真实数据');
            document.getElementById('uploadArea').style.display = 'none';
            setStatus(true);
            btn.disabled = false;
            btn.textContent = '🔄 刷新数据';
            return;
        }
    } catch {}

    // 本地服务离线
    setStatus(false);
    
    // 本地服务离线，直接显示上传区域
    document.getElementById('uploadArea').style.display = 'block';
    document.getElementById('tableContainer').innerHTML = '<div class="tips"><h4>📤 上传数据文件</h4><p>请从 <code>~/.workbuddy/traces/</code> 目录复制 JSON 文件上传</p></div>';
    document.getElementById('analysisContent').innerHTML = '<div class="tips"><p>上传文件后即可查看统计</p></div>';
    btn.disabled = false;
    btn.textContent = '🔄 刷新数据';
}

function updateChart(weeks) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    if (chart) chart.destroy();
    if (!weeks || weeks.length === 0) {
        ctx.canvas.parentNode.innerHTML = '<div class="loading">暂无数据</div>';
        return;
    }
    const labels = weeks.map(w => w.week + ' (' + w.dateRange + ')');
    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {label: '输入 Tokens', data: weeks.map(w => w.input), backgroundColor: 'rgba(99,102,241,0.8)'},
                {label: '输出 Tokens', data: weeks.map(w => w.output), backgroundColor: 'rgba(16,185,129,0.8)'},
                {label: '缓存 Tokens', data: weeks.map(w => w.cached), backgroundColor: 'rgba(245,158,11,0.6)'}
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {legend: {position: 'top'}},
            scales: {x: {stacked: true}, y: {stacked: true, beginAtZero: true}}
        }
    });
}

function updateTable(weeks, summary) {
    if (!weeks || weeks.length === 0) {
        document.getElementById('tableContainer').innerHTML = '<div class="loading">暂无数据</div>';
        return;
    }
    let html = '<table><thead><tr><th>周次</th><th>日期范围</th><th>输入</th><th>输出</th><th>缓存</th><th>合计</th></tr></thead><tbody>';
    for (const w of weeks) {
        html += '<tr><td><span class="week-tag">' + w.week + '</span></td><td>' + w.dateRange + '</td><td class="num">' + fmt(w.input) + '</td><td class="num">' + fmt(w.output) + '</td><td class="num">' + fmt(w.cached) + '</td><td class="num">' + fmt(w.total) + '</td></tr>';
    }
    html += '<tr class="total-row"><td colspan="2">合计</td><td class="num">' + fmt(summary.totalInput) + '</td><td class="num">' + fmt(summary.totalOutput) + '</td><td class="num">' + fmt(summary.totalCached) + '</td><td class="num">' + fmt(summary.total) + '</td></tr></tbody></table>';
    document.getElementById('tableContainer').innerHTML = html;
}

function generateAnalysis(d) {
    const weeks = d.weeks || [];
    const summary = d.summary || {};
    if (weeks.length === 0) {
        document.getElementById('analysisContent').innerHTML = '<div class="tips"><p>暂无数据</p></div>';
        return;
    }
    const avg = summary.total / weeks.length;
    const last = weeks[weeks.length - 1];
    let trend = '';
    if (weeks.length > 1) {
        const c = ((last.total - weeks[0].total) / weeks[0].total * 100).toFixed(1);
        trend = c > 0 ? '较首周增加 ' + c + '%' : '较首周减少 ' + Math.abs(c) + '%';
    }
    const html = '<div class="tips"><h4>📊 使用分析</h4><ul><li><strong>使用频率：</strong>在 ' + (summary.days || 0) + ' 天内，共有 ' + weeks.length + ' 周有使用记录。</li><li><strong>周均使用：</strong>平均每周使用 ' + (avg / 1000000).toFixed(1) + 'M tokens。</li><li><strong>缓存效率：</strong>整体缓存复用率达到 ' + (summary.cacheRate || 0) + '%。</li><li><strong>趋势：</strong>' + (trend || '数据不足') + '</li></ul><h4 style="margin-top:16px">🎯 优化建议</h4><ul><li><strong>缓存利用：</strong>继续保持同一主题对话的连贯性，提高缓存复用率。</li><li><strong>任务合并：</strong>将相关任务放在一起处理。</li><li><strong>定期清理：</strong>完成的主题及时开启新会话。</li></ul></div>';
    document.getElementById('analysisContent').innerHTML = html;
}

// 页面加载后自动获取数据
window.addEventListener('DOMContentLoaded', function() {
    loadData();
});
</script>
</body>
</html>'''

@app.route('/')
def index():
    today = datetime.now().date()
    start_of_month = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    return HTML_PAGE.replace('{{START_DATE}}', start_of_month).replace('{{END_DATE}}', end_date)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/stats')
def stats():
    try:
        start_str = request.args.get('start', datetime.now().strftime('%Y-%m-01'))
        end_str = request.args.get('end', datetime.now().strftime('%Y-%m-%d'))
        
        start = datetime.strptime(start_str, '%Y-%m-%d').date()
        end = datetime.strptime(end_str, '%Y-%m-%d').date()
        
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
                                    week_key = monday.strftime('%Y-W%W')
                                    
                                    if week_key not in week_data:
                                        week_data[week_key] = {
                                            'week': week_key,
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
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
