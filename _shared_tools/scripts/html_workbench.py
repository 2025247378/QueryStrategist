"""Offline HTML shell and interactions for QueryStrategist deliverables."""

import html


PAGE_META = {
    "scope_card": ("范围卡", "研究范围", "确认对象、技术、任务、排除项与检索边界。"),
    "query_pack": ("检索式", "多平台检索式", "按数据库查看、复制并验证可直接使用的检索式。"),
    "candidate_list": ("候选文献", "文献候选清单", "搜索、筛选和排序 API 收割的待核验文献。"),
    "usage_guide": ("使用说明", "检索使用说明", "查看各平台填入位置以及调宽、调窄方法。"),
}

ICONS = {
    "print": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/></svg>',
    "arrow": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg>',
}

CSS = r"""
:root{color-scheme:light;--ink:#1f2933;--muted:#667784;--navy:#24557a;--teal:#147d78;--orange:#c65f2c;--green:#2f7d4a;--line:#d9e2e8;--soft:#f4f7f9;--paper:#fff}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--ink);background:var(--paper);font:15px/1.72 "Microsoft YaHei","Noto Sans CJK SC",Arial,sans-serif;letter-spacing:0}
a{color:#006b8f;text-underline-offset:3px}button,input,select{font:inherit;letter-spacing:0}:focus-visible{outline:3px solid rgba(198,95,44,.38);outline-offset:2px}
.icon{width:18px;height:18px;flex:0 0 18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.topbar{position:sticky;top:0;z-index:30;display:grid;grid-template-columns:minmax(210px,1fr) auto minmax(120px,1fr);align-items:center;min-height:58px;padding:0 28px;border-bottom:1px solid var(--line);background:rgba(255,255,255,.97)}
.brand{display:inline-flex;align-items:center;gap:10px;color:var(--ink);text-decoration:none;font-weight:700}.brand-mark{width:26px;height:26px;display:grid;place-items:center;color:#fff;background:var(--navy);border-radius:5px;font:700 13px/1 Arial,sans-serif}
.primary-nav{display:flex;align-items:center;gap:4px;scrollbar-width:none}.primary-nav::-webkit-scrollbar{display:none}.primary-nav a{padding:8px 10px;color:#52636f;text-decoration:none;border-radius:4px;white-space:nowrap}.primary-nav a:hover{background:var(--soft);color:var(--ink)}.primary-nav a[aria-current=page]{color:var(--navy);background:#eaf1f5;font-weight:700}
.header-actions{justify-self:end}.icon-button{display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;padding:0;color:#52636f;background:transparent;border:1px solid transparent;border-radius:4px;cursor:pointer}.icon-button:hover{color:var(--navy);background:var(--soft);border-color:var(--line)}
.page-layout{display:grid;grid-template-columns:220px minmax(0,920px);gap:42px;max-width:1220px;margin:0 auto;padding:34px 32px 72px}.toc-inner{position:sticky;top:92px}.toc-title{margin:0 0 10px;color:var(--muted);font-size:12px;font-weight:700}.toc nav{display:grid;gap:2px;border-left:1px solid var(--line)}.toc a{display:block;padding:6px 10px;color:#647581;text-decoration:none;line-height:1.4;border-left:2px solid transparent;margin-left:-1px}.toc a.sub{padding-left:22px;font-size:13px}.toc a:hover{color:var(--navy);border-left-color:var(--orange)}
.document{min-width:0}.document>h1:first-child{margin-top:0}h1,h2,h3,h4{color:#183c58;line-height:1.32;overflow-wrap:anywhere}h1{margin:0 0 22px;padding-bottom:14px;border-bottom:3px solid var(--orange);font-size:30px}h2{margin:38px 0 14px;padding-bottom:7px;border-bottom:1px solid var(--line);font-size:21px}h3{margin:26px 0 10px;font-size:17px}p{margin:10px 0 16px}ul,ol{margin:10px 0 18px;padding-left:24px}li{margin:5px 0}hr{margin:32px 0;border:0;border-top:1px solid var(--line)}
code{font-family:Consolas,"Courier New",monospace;background:#eef3f5;padding:2px 5px;border-radius:3px;overflow-wrap:anywhere}.code-shell{position:relative;margin:14px 0 22px}pre{min-height:72px;margin:0;overflow:auto;padding:46px 16px 16px;color:#162832;background:#f2f6f7;border:1px solid #cfdae0;border-left:4px solid var(--teal);border-radius:5px}pre code{display:block;min-width:max-content;padding:0;background:transparent;white-space:pre;overflow-wrap:normal}
.copy-button{position:absolute;top:8px;right:8px;display:inline-flex;align-items:center;gap:6px;min-width:78px;height:30px;padding:0 10px;color:#425762;background:#fff;border:1px solid #c7d3d9;border-radius:4px;cursor:pointer}.copy-button:hover{color:var(--navy);border-color:#91a8b5}.copy-button.copied{color:var(--green);border-color:#9fc5aa}
blockquote{margin:18px 0;padding:12px 16px;color:#56371f;background:#fff8f2;border-left:4px solid var(--orange)}.table-wrap{width:100%;overflow:auto;margin:16px 0 24px;border:1px solid var(--line)}table{width:100%;min-width:680px;border-collapse:collapse;background:#fff}th,td{padding:9px 11px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);overflow-wrap:anywhere}th{position:sticky;top:0;z-index:2;color:#29485d;background:#eaf1f5;font-weight:700}tbody tr:nth-child(even){background:#f8fafb}tbody tr:hover{background:#fff9f3}
[data-page=candidate_list] table{min-width:960px;font-size:14px}[data-page=candidate_list] th:nth-child(1),[data-page=candidate_list] td:nth-child(1){min-width:310px}[data-page=candidate_list] th:nth-child(2),[data-page=candidate_list] td:nth-child(2){min-width:110px}[data-page=candidate_list] th:nth-child(3),[data-page=candidate_list] td:nth-child(3){width:72px;min-width:72px;white-space:nowrap}[data-page=candidate_list] th:nth-child(4),[data-page=candidate_list] td:nth-child(4){min-width:132px}[data-page=candidate_list] th:nth-child(5),[data-page=candidate_list] td:nth-child(5){min-width:150px}[data-page=candidate_list] th:nth-child(6),[data-page=candidate_list] td:nth-child(6){min-width:92px}
.tabs{display:flex;gap:4px;width:100%;overflow-x:auto;margin:18px 0;padding-bottom:4px;border-bottom:1px solid var(--line);scrollbar-width:none;scroll-snap-type:x proximity}.tabs::-webkit-scrollbar{display:none}.tab-button{flex:0 0 auto;min-height:38px;padding:7px 12px;color:#566874;background:transparent;border:1px solid transparent;border-radius:4px 4px 0 0;cursor:pointer;scroll-snap-align:start}.tab-button:hover{background:var(--soft)}.tab-button.active{color:var(--navy);background:#eaf1f5;border-color:#cddae1;border-bottom-color:#eaf1f5;font-weight:700}.platform-panel[hidden]{display:none}
.data-tools{margin:18px 0 20px;padding:16px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.metric-strip{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:1px;margin-bottom:14px;background:var(--line);border:1px solid var(--line)}.metric{min-width:0;padding:10px 12px;background:#fff}.metric span{display:block;color:var(--muted);font-size:12px}.metric strong{display:block;margin-top:2px;color:#193f5b;font-size:21px}
.filter-row{display:grid;grid-template-columns:minmax(220px,1fr) 150px 130px 105px 105px;gap:8px}.field{display:grid;gap:4px;min-width:0}.field label{color:var(--muted);font-size:12px}.field input,.field select{width:100%;height:38px;min-width:0;padding:6px 9px;color:var(--ink);background:#fff;border:1px solid #bfcdd5;border-radius:4px}.result-count{margin:10px 0 0;color:var(--muted);font-size:13px}.sort-button{width:100%;padding:0;text-align:left;color:inherit;background:transparent;border:0;cursor:pointer;font-weight:inherit}.sort-button[data-direction=asc]::after{content:"  ↑";color:var(--orange)}.sort-button[data-direction=desc]::after{content:"  ↓";color:var(--orange)}
.home-main{max-width:1120px;margin:0 auto;padding:48px 32px 72px}.home-kicker{margin:0 0 7px;color:var(--orange);font-weight:700}.home-main h1{max-width:760px;margin-bottom:12px}.home-lead{max-width:760px;color:#526570;font-size:17px}.summary-band{display:grid;grid-template-columns:repeat(3,1fr);margin:28px 0 36px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.summary-item{padding:15px 18px;border-right:1px solid var(--line)}.summary-item:last-child{border-right:0}.summary-item span{display:block;color:var(--muted);font-size:12px}.summary-item strong{display:block;margin-top:3px;color:#204a68}
.launch-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.launch-card{display:grid;grid-template-columns:1fr auto;gap:18px;min-height:148px;padding:22px;color:var(--ink);text-decoration:none;border:1px solid var(--line);border-radius:6px}.launch-card:hover{border-color:#97aeba;background:#f8fafb}.launch-card h2{margin:0 0 7px;padding:0;border:0;font-size:19px}.launch-card p{margin:0;color:var(--muted)}.launch-card .icon{align-self:center;width:22px;height:22px;color:var(--teal)}.home-note{margin-top:24px;padding:13px 16px;color:#4b5f6a;background:#f3f7f8;border-left:4px solid var(--teal)}.noscript{padding:10px 16px;color:#603f1f;background:#fff6e8;border-bottom:1px solid #e7c99a}
@media(max-width:980px){.topbar{grid-template-columns:auto 1fr auto;padding:0 16px}.primary-nav{justify-self:end;max-width:56vw;overflow-x:auto}.page-layout{grid-template-columns:1fr;padding:28px 22px 58px}.toc{display:none}.filter-row{grid-template-columns:minmax(180px,1fr) repeat(2,130px)}}
@media(max-width:680px){.topbar{grid-template-columns:1fr auto;min-height:54px}.primary-nav{grid-column:1/-1;justify-self:stretch;max-width:none;order:3;padding:4px 0 8px}.brand{padding-top:8px}.page-layout,.home-main{padding:24px 16px 48px}h1{font-size:25px}h2{font-size:19px}.metric-strip{grid-template-columns:repeat(2,1fr)}.metric:last-child{grid-column:1/-1}.filter-row{grid-template-columns:1fr 1fr}.filter-row .field:first-child{grid-column:1/-1}.summary-band{grid-template-columns:1fr}.summary-item{border-right:0;border-bottom:1px solid var(--line)}.launch-grid{grid-template-columns:1fr}.launch-card{min-height:132px}}
@media print{.topbar,.toc,.tabs,.copy-button,.data-tools,.noscript{display:none!important}body{color:#000;background:#fff;font-size:11pt}.page-layout{display:block;max-width:none;padding:0}.document{width:100%}pre{white-space:pre-wrap;break-inside:avoid}.table-wrap{overflow:visible;border:0}table{min-width:0;font-size:9pt}a{color:#000;text-decoration:none}}
"""

JS = r"""
(function(){'use strict';
const copyIcon='<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>';
const checkIcon='<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m20 6-11 11-5-5"/></svg>';
function slug(text,index){return text.trim().toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g,'-').replace(/^-|-$/g,'')||'section-'+index}
function links(){document.querySelectorAll('a[href^="http"]').forEach(a=>{a.target='_blank';a.rel='noopener noreferrer'})}
function copyButtons(){document.querySelectorAll('pre').forEach(pre=>{const shell=document.createElement('div');shell.className='code-shell';pre.parentNode.insertBefore(shell,pre);shell.appendChild(pre);const b=document.createElement('button');b.type='button';b.className='copy-button';b.title='复制检索式';b.innerHTML=copyIcon+'<span>复制</span>';b.onclick=async()=>{try{const text=pre.textContent;if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(text)}else{const area=document.createElement('textarea');area.value=text;area.style.cssText='position:fixed;opacity:0';document.body.appendChild(area);area.select();document.execCommand('copy');area.remove()}b.classList.add('copied');b.innerHTML=checkIcon+'<span>已复制</span>';setTimeout(()=>{b.classList.remove('copied');b.innerHTML=copyIcon+'<span>复制</span>'},1600)}catch(e){b.querySelector('span').textContent='复制失败'}};shell.appendChild(b)})}
function queryTabs(){const article=document.querySelector('[data-page="query_pack"]');if(!article)return;const pattern=/web of science|wos|scopus|ieee|google scholar|cnki|知网|万方|wanfang/i;const heads=Array.from(article.querySelectorAll(':scope>h2')).filter(h=>pattern.test(h.textContent));if(heads.length<2)return;const tabs=document.createElement('div');tabs.className='tabs';tabs.setAttribute('role','tablist');const panels=[];heads.forEach((head,index)=>{const panel=document.createElement('section');panel.className='platform-panel';panel.id='platform-'+index;head.parentNode.insertBefore(panel,head);panel.appendChild(head);while(panel.nextSibling&&panel.nextSibling.tagName!=='H2'&&!panel.nextSibling.classList?.contains('platform-panel'))panel.appendChild(panel.nextSibling);panel.hidden=index!==0;panels.push(panel);const b=document.createElement('button');b.type='button';b.className='tab-button'+(index===0?' active':'');b.setAttribute('role','tab');b.setAttribute('aria-selected',index===0?'true':'false');b.textContent=head.textContent;b.onclick=()=>{panels.forEach((p,i)=>p.hidden=i!==index);tabs.querySelectorAll('button').forEach((x,i)=>{x.classList.toggle('active',i===index);x.setAttribute('aria-selected',i===index?'true':'false')})};tabs.appendChild(b)});panels[0].parentNode.insertBefore(tabs,panels[0])}
function candidateTools(){const article=document.querySelector('[data-page="candidate_list"]');if(!article)return;const table=article.querySelector('table');if(!table||!table.tBodies.length)return;const rows=Array.from(table.tBodies[0].rows);const headers=Array.from(table.tHead?.rows[0]?.cells||[]).map(c=>c.textContent.trim().toLowerCase());const find=words=>headers.findIndex(v=>words.some(w=>v.includes(w)));const yearCol=find(['year','年份','年']);const statusCol=find(['verification','status','验证','状态']);const oaCol=find(['oa']);const status=row=>{const t=(statusCol>=0?row.cells[statusCol]?.textContent:row.textContent).toLowerCase();if(t.includes('unverified')||t.includes('待人工'))return'pending';if(t.includes('dropped')||t.includes('已剔除'))return'dropped';if(t.includes('verified')||t.includes('已验证'))return'verified';return'unknown'};const oa=row=>{const t=(oaCol>=0?row.cells[oaCol]?.textContent:row.textContent).toLowerCase();if(t.includes('非oa')||t.includes('closed')||t.includes('false'))return'closed';if(t.includes('oa')||/gold|green|hybrid|bronze|open/.test(t))return'open';return'unknown'};const tools=document.createElement('section');tools.className='data-tools';const verified=rows.filter(r=>status(r)==='verified').length,pending=rows.filter(r=>status(r)==='pending').length,open=rows.filter(r=>oa(r)==='open').length,closed=rows.filter(r=>oa(r)==='closed').length;tools.innerHTML='<div class="metric-strip"><div class="metric"><span>候选总数</span><strong>'+rows.length+'</strong></div><div class="metric"><span>已验证</span><strong>'+verified+'</strong></div><div class="metric"><span>待人工核验</span><strong>'+pending+'</strong></div><div class="metric"><span>开放获取</span><strong>'+open+'</strong></div><div class="metric"><span>非开放获取</span><strong>'+closed+'</strong></div></div><div class="filter-row"><div class="field"><label for="candidate-search">标题、作者或 DOI</label><input id="candidate-search" type="search" placeholder="搜索候选文献"></div><div class="field"><label for="status-filter">验证状态</label><select id="status-filter"><option value="">全部</option><option value="verified">已验证</option><option value="pending">待人工核验</option><option value="dropped">已剔除</option></select></div><div class="field"><label for="oa-filter">OA 状态</label><select id="oa-filter"><option value="">全部</option><option value="open">开放获取</option><option value="closed">非开放获取</option><option value="unknown">未知</option></select></div><div class="field"><label for="year-min">起始年份</label><input id="year-min" type="number" placeholder="2016"></div><div class="field"><label for="year-max">截止年份</label><input id="year-max" type="number" placeholder="2026"></div></div><p class="result-count" aria-live="polite"></p>';const wrap=table.closest('.table-wrap');wrap.parentNode.insertBefore(tools,wrap);const search=tools.querySelector('#candidate-search'),sf=tools.querySelector('#status-filter'),of=tools.querySelector('#oa-filter'),ymin=tools.querySelector('#year-min'),ymax=tools.querySelector('#year-max'),count=tools.querySelector('.result-count');function filter(){const q=search.value.trim().toLocaleLowerCase('zh-CN'),min=Number(ymin.value)||-Infinity,max=Number(ymax.value)||Infinity;let visible=0;rows.forEach(row=>{const y=yearCol>=0?Number((row.cells[yearCol]?.textContent||'').match(/\d{4}/)?.[0]):0;const show=(!q||row.textContent.toLocaleLowerCase('zh-CN').includes(q))&&(!sf.value||status(row)===sf.value)&&(!of.value||oa(row)===of.value)&&(!y||(y>=min&&y<=max));row.hidden=!show;if(show)visible++});count.textContent='当前显示 '+visible+' / '+rows.length+' 条'}[search,sf,of,ymin,ymax].forEach(c=>c.addEventListener(c.tagName==='SELECT'?'change':'input',filter));filter();Array.from(table.tHead?.rows[0]?.cells||[]).forEach((cell,col)=>{const label=cell.textContent.trim(),b=document.createElement('button');b.type='button';b.className='sort-button';b.textContent=label;b.title='按'+label+'排序';b.onclick=()=>{const direction=b.dataset.direction==='asc'?'desc':'asc';table.querySelectorAll('.sort-button').forEach(x=>delete x.dataset.direction);b.dataset.direction=direction;rows.sort((l,r)=>{const a=l.cells[col]?.textContent.trim()||'',z=r.cells[col]?.textContent.trim()||'';const an=Number(a.replace(/[^0-9.-]/g,'')),zn=Number(z.replace(/[^0-9.-]/g,''));const cmp=Number.isFinite(an)&&Number.isFinite(zn)&&a&&z?an-zn:a.localeCompare(z,'zh-CN',{numeric:true});return direction==='asc'?cmp:-cmp});rows.forEach(row=>table.tBodies[0].appendChild(row))};cell.textContent='';cell.appendChild(b)})}
function toc(){const article=document.querySelector('.document'),nav=document.querySelector('#toc-nav');if(!article||!nav)return;Array.from(article.querySelectorAll('h2,h3')).filter(h=>!h.closest('[hidden]')).forEach((h,i)=>{if(!h.id)h.id=slug(h.textContent,i);const a=document.createElement('a');a.href='#'+h.id;a.textContent=h.textContent;if(h.tagName==='H3')a.className='sub';nav.appendChild(a)})}
document.addEventListener('DOMContentLoaded',()=>{links();queryTabs();copyButtons();candidateTools();toc();const p=document.querySelector('#print-page');if(p)p.onclick=()=>window.print()});})();
"""


def _navigation(active_page, available_pages):
    current = ' aria-current="page"' if active_page == "index" else ""
    links = [f'<a href="index.html"{current}>总览</a>']
    for key in available_pages:
        label = PAGE_META[key][0]
        current = ' aria-current="page"' if active_page == key else ""
        links.append(f'<a href="{key}.html"{current}>{label}</a>')
    return "".join(links)


def shell(title, content, page_key, available_pages, home=False):
    print_button = "" if home else (
        f'<button id="print-page" class="icon-button" type="button" title="打印本页" aria-label="打印本页">{ICONS["print"]}</button>'
    )
    main = content if home else (
        '<main class="page-layout"><aside class="toc" aria-label="本页目录"><div class="toc-inner">'
        '<p class="toc-title">本页目录</p><nav id="toc-nav"></nav></div></aside>'
        f'<article class="document" data-page="{page_key}">{content}</article></main>'
    )
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; img-src data:">'
        f'<title>{html.escape(title)} | QueryStrategist</title><style>{CSS}</style></head><body>'
        '<header class="topbar"><a class="brand" href="index.html"><span class="brand-mark">QS</span><span>QueryStrategist</span></a>'
        f'<nav class="primary-nav" aria-label="主要导航">{_navigation(page_key, available_pages)}</nav>'
        f'<div class="header-actions">{print_button}</div></header>'
        '<noscript><div class="noscript">交互增强未启用，全部文档内容仍可正常阅读。</div></noscript>'
        f'{main}<script>{JS}</script></body></html>\n'
    )


def index_page(available_pages):
    cards = []
    for key in available_pages:
        _, title, description = PAGE_META[key]
        cards.append(
            f'<a class="launch-card" href="{key}.html"><div><h2>{title}</h2><p>{description}</p></div>{ICONS["arrow"]}</a>'
        )
    content = (
        '<main class="home-main"><p class="home-kicker">离线检索工作台</p><h1>检索策略包</h1>'
        '<p class="home-lead">从范围确认到检索式执行，再到候选文献筛选。所有页面均可离线打开，检索式可直接复制。</p>'
        '<section class="summary-band" aria-label="交付摘要">'
        f'<div class="summary-item"><span>交付模块</span><strong>{len(available_pages)} 项</strong></div>'
        '<div class="summary-item"><span>阅读格式</span><strong>离线 HTML</strong></div>'
        '<div class="summary-item"><span>可编辑源文件</span><strong>Markdown + CSV</strong></div></section>'
        f'<section class="launch-grid" aria-label="策略包内容">{"".join(cards)}</section>'
        '<p class="home-note">建议先确认研究范围，再复制检索式。候选文献仅供筛选，正式引用前仍需在数据库核验。</p></main>'
    )
    return shell("检索策略包", content, "index", available_pages, home=True)
