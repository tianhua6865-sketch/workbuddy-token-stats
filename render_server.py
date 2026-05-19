#!/usr/bin/env python3
"""WorkBuddy Token Stats - 纯前端版本，支持选择本地文件夹"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

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
header p{color:#64748b;font-size:0.9rem}
.card{background:#fff;border-radius:16px;padding:24px;margin-bottom:24px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}
.card-title{font-size:1.1rem;font-weight:600;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.card-title::before{content:'';width:4px;height:20px;background:#6366f1;border-radius:2px}
.date-picker{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:16px}
.date-input{display:flex;align-items:center;gap:8px}
.date-input label{font-weight:500;color:#64748b;font-size:0.9rem}
.date-input input{padding:8px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:0.95rem}
.btn{padding:10px 20px;background:#6366f1;color:white;border:none;border-radius:8px;font-size:1rem;cursor:pointer}
.btn:hover{background:#818cf8}
.btn-green{background:#10b981}
.btn-green:hover{background:#34d399}
.drop-zone{border:2px dashed #cbd5e1;border-radius:12px;padding:40px;text-align:center;cursor:pointer;transition:all 0.3s}
.drop-zone:hover{border-color:#6366f1;background:#f8fafc}
.drop-zone.dragover{border-color:#6366f1;background:#e0e7ff}
.drop-zone p{margin:8px 0;color:#64748b}
.drop-zone .hint{font-size:0.85rem;color:#94a3b8}
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
.tips li::before{content:'';position:absolute;left:0;font-size:0.9rem}
.loading{text-align:center;padding:40px;color:#64748b}
.last-update{text-align:right;font-size:0.8rem;color:#64748b;margin-top:8px}
.hidden{display:none}
</style>
</head>
<body>
<div class="container">
<header><h1>WorkBuddy Token 使用量统计</h1><p>选择本地 traces 文件夹，分析 Token 使用情况</p></header>

<div class="card" id="selectCard">
<div class="card-title">选择数据源</div>
<div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
<p>点击选择文件夹 或 拖拽文件夹到此处</p>
<p class="hint">请选择 ~/.workbuddy/traces/ 文件夹</p>
</div>
<input type="file" id="fileInput" webkitdirectory multiple style="display:none" onchange="handleFolderSelect(this.files)">
<div style="margin-top:16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap">
<div class="date-input">
<label>开始日期：</label><input type="date" id="startDate">
</div>
<div class="date-input">
<label>结束日期：</label><input type="date" id="endDate">
</div>
</div>
<div id="fileInfo" style="margin-top:16px;font-size:0.9rem;color:#64748b"></div>
</div>

<div id="dataCard" class="card hidden">
<div class="card-title">统计概览</div>
<div class="stats-grid">
<div class="stat-card"><div class="stat-label">总使用量</div><div class="stat-value" id="totalTokens">--</div><div class="stat-sub">Tokens</div></div>
<div class="stat-card success"><div class="stat-label">缓存复用率</div><div class="stat-value" id="cacheRate">--</div><div class="stat-sub">节省成本</div></div>
<div class="stat-card warning"><div class="stat-label">活跃周数</div><div class="stat-value" id="activeWeeks">--</div><div class="stat-sub">周</div></div>
<div class="stat-card"><div class="stat-label">日均使用</div><div class="stat-value" id="dailyAvg">--</div><div class="stat-sub">Tokens/天</div></div>
</div>
<div class="last-update" id="lastUpdate"></div>
</div>

<div id="chartCard" class="card hidden">
<div class="card-title">每周使用量趋势</div>
<div class="chart-container"><canvas id="trendChart"></canvas></div>
</div>

<div id="tableCard" class="card hidden">
<div class="card-title">详细统计表</div>
<div id="tableContainer"><div class="loading">暂无数据</div></div>
</div>

<div id="analysisCard" class="card hidden">
<div class="card-title">分析结果与优化建议</div>
<div id="analysisContent"></div>
</div>

<div class="card hidden" id="changeFolder">
<button class="btn" onclick="resetPage()">选择其他文件夹</button>
</div>
</div>

<script>
let chart = null;
let currentData = null;

const today = new Date();
const first = new Date(today.getFullYear(), today.getMonth(), 1);
document.getElementById('startDate').value = first.toISOString().split('T')[0];
document.getElementById('endDate').value = today.toISOString().split('T')[0];

const dropZone = document.getElementById('dropZone');
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('dragover'); handleFolderSelect(e.dataTransfer.files); });

function fmt(n) { return (n || 0).toLocaleString(); }

let totalInput = 0, totalOutput = 0, totalCached = 0;
const weekData = {};

function handleFolderSelect(files) {
    if (!files || files.length === 0) return;
    document.getElementById('fileInfo').textContent = '已选择 ' + files.length + ' 个文件，正在解析...';

    totalInput = 0; totalOutput = 0; totalCached = 0;
    for (const key in weekData) delete weekData[key];

    let processed = 0;
    for (const file of files) {
        if (!file.name.endsWith('.json')) { processed++; if (processed === files.length) finishParsing(); continue; }
        const reader = new FileReader();
        reader.onload = e => {
            try {
                const data = JSON.parse(e.target.result);
                const trace = data.trace || {};
                const startedAt = trace.startedAt;
                if (startedAt) {
                    const traceDate = new Date(startedAt);
                    const startDate = new Date(document.getElementById('startDate').value);
                    const endDate = new Date(document.getElementById('endDate').value);
                    if (traceDate >= startDate && traceDate <= endDate) {
                        const m = trace.modelInfo || {};
                        const inp = m.totalInputTokens || 0;
                        const out = m.totalOutputTokens || 0;
                        const cached = m.totalCachedTokens || 0;
                        totalInput += inp; totalOutput += out; totalCached += cached;

                        const day = traceDate.getDay();
                        const monday = new Date(traceDate);
                        monday.setDate(traceDate.getDate() - (day === 0 ? 6 : day - 1));
                        const sunday = new Date(monday);
                        sunday.setDate(monday.getDate() + 6);
                        const wk = monday.toISOString().split('T')[0];
                        if (!weekData[wk]) weekData[wk] = {week: monday.getFullYear()+'-W'+getWeek(monday), dateRange: fmtMD(monday)+' ~ '+fmtMD(sunday), input:0,output:0,cached:0,total:0};
                        weekData[wk].input += inp; weekData[wk].output += out; weekData[wk].cached += cached; weekData[wk].total += inp+out;
                    }
                }
            } catch(err) {}
            if (++processed === files.length) finishParsing();
        };
        reader.readAsText(file);
    }
}

function finishParsing() {
    const start = document.getElementById('startDate').value;
    const end = document.getElementById('endDate').value;
    const startDate = new Date(start);
    const endDate = new Date(end);
    const weeks = Object.values(weekData).sort((a,b)=>a.week.localeCompare(b.week));
    const total = totalInput + totalOutput;
    const days = Math.round((endDate - startDate) / 86400000) + 1;

    currentData = {period: start+' ~ '+end, weeks, summary:{total,totalInput,totalOutput,totalCached,cacheRate:Math.round(totalCached/max(total,1)*100*10)/10,activeWeeks:weeks.length,dailyAvg:Math.round(total/max(days,1)),days}};

    document.getElementById('fileInfo').textContent = '已解析 ' + weeks.length + ' 周数据，共 ' + fmt(total) + ' Tokens';
    renderData();
}

function renderData() {
    const d = currentData;
    document.getElementById('totalTokens').textContent = fmt(d.summary.total);
    document.getElementById('cacheRate').textContent = (d.summary.cacheRate || 0) + '%';
    document.getElementById('activeWeeks').textContent = d.summary.activeWeeks || 0;
    document.getElementById('dailyAvg').textContent = fmt(d.summary.dailyAvg);
    document.getElementById('lastUpdate').textContent = '数据区间: ' + d.period;
    ['dataCard','chartCard','tableCard','analysisCard','changeFolder'].forEach(id => document.getElementById(id).classList.remove('hidden'));
    updateChart(d.weeks);
    updateTable(d.weeks, d.summary);
    generateAnalysis(d);
}

function getWeek(d) { const dn=d.getUTCDay()||7;const y=new Date(Date.UTC(d.getUTCFullYear(),0,1));return Math.ceil((((d-y)/86400000+1))/7); }
function fmtMD(d) { return (d.getMonth()+1).toString().padStart(2,'0')+'-'+d.getDate().toString().padStart(2,'0'); }

function updateChart(weeks) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    if (chart) chart.destroy();
    if (!weeks || !weeks.length) { ctx.canvas.parentNode.innerHTML='<div class=loading>暂无数据</div>'; return; }
    chart = new Chart(ctx, {type:'bar',data:{labels:weeks.map(w=>w.week+' ('+w.dateRange+')'),datasets:[{label:'输入',data:weeks.map(w=>w.input),backgroundColor:'rgba(99,102,241,0.8)'},{label:'输出',data:weeks.map(w=>w.output),backgroundColor:'rgba(16,185,129,0.8)'},{label:'缓存',data:weeks.map(w=>w.cached),backgroundColor:'rgba(245,158,11,0.6)'}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top'}},scales:{x:{stacked:true},y:{stacked:true,beginAtZero:true}}}});
}

function updateTable(weeks, summary) {
    if (!weeks || !weeks.length) { document.getElementById('tableContainer').innerHTML='<div class=loading>暂无数据</div>'; return; }
    let html = '<table><thead><tr><th>周次</th><th>日期</th><th>输入</th><th>输出</th><th>缓存</th><th>合计</th></tr></thead><tbody>';
    for (const w of weeks) html += '<tr><td><span class=week-tag>'+w.week+'</span></td><td>'+w.dateRange+'</td><td class=num>'+fmt(w.input)+'</td><td class=num>'+fmt(w.output)+'</td><td class=num>'+fmt(w.cached)+'</td><td class=num>'+fmt(w.total)+'</td></tr>';
    html += '<tr class=total-row><td colspan=2>合计</td><td class=num>'+fmt(summary.totalInput)+'</td><td class=num>'+fmt(summary.totalOutput)+'</td><td class=num>'+fmt(summary.totalCached)+'</td><td class=num>'+fmt(summary.total)+'</td></tr></tbody></table>';
    document.getElementById('tableContainer').innerHTML = html;
}

function generateAnalysis(d) {
    const weeks = d.weeks || [], summary = d.summary || {};
    if (!weeks.length) { document.getElementById('analysisContent').innerHTML='<div class=loading>暂无数据</div>'; return; }
    const avg = summary.total / weeks.length;
    let trend = '';
    if (weeks.length > 1) { const c = ((weeks[weeks.length-1].total - weeks[0].total) / weeks[0].total * 100).toFixed(1); trend = c > 0 ? '较首周增加 '+c+'%' : '较首周减少 '+Math.abs(c)+'%'; }
    document.getElementById('analysisContent').innerHTML = '<div class=tips><h4>使用分析</h4><ul><li>使用频率：在 '+(summary.days||0)+' 天内共有 '+weeks.length+' 周使用记录</li><li>周均使用：'+(avg/1000000).toFixed(1)+'M tokens</li><li>缓存效率：'+(summary.cacheRate||0)+'%</li><li>趋势：'+(trend||'数据不足')+'</li></ul><h4 style=margin-top:16px>优化建议</h4><ul><li>保持同一主题对话连贯性，提高缓存复用率</li><li>将相关任务放在一起处理</li><li>完成的主题及时开启新会话</li></ul></div>';
}

function resetPage() {
    ['dataCard','chartCard','tableCard','analysisCard','changeFolder'].forEach(id => document.getElementById(id).classList.add('hidden'));
    document.getElementById('fileInfo').textContent = '';
    document.getElementById('fileInput').value = '';
    currentData = null;
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
