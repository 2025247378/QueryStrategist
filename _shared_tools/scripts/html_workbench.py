"""Offline HTML shell and interactions for QueryStrategist deliverables."""

import html


PAGE_META = {
    "scope_card": (
        "范围卡",
        "研究范围",
        "确认对象、技术、任务、排除项与检索边界。",
        "target",
    ),
    "query_pack": (
        "检索式",
        "多平台检索式",
        "按数据库查看、复制并验证检索式。",
        "code",
    ),
    "candidate_list": (
        "候选文献",
        "文献候选清单",
        "搜索、筛选和排序 API 收割的待核验文献。",
        "list",
    ),
    "usage_guide": (
        "使用说明",
        "检索使用说明",
        "查看各平台填入位置以及调宽、调窄方法。",
        "book",
    ),
}

PAGE_I18N = {
    "scope_card": ("nav_scope_card", "scope_title", "scope_desc"),
    "query_pack": ("nav_query_pack", "queries_title", "queries_desc"),
    "candidate_list": ("nav_candidate_list", "candidates_title", "candidates_desc"),
    "usage_guide": ("nav_usage_guide", "guide_title", "guide_desc"),
}

WRITING_TYPE_I18N = {
    "综述": "writing_review",
    "review": "writing_review",
    "literature review": "writing_review",
    "研究论著": "writing_research_article",
    "研究论著/实验研究": "writing_research_article",
    "研究论著 / 实验研究": "writing_research_article",
    "实验研究": "writing_research_article",
    "research article": "writing_research_article",
    "research paper": "writing_research_article",
    "experimental study": "writing_research_article",
    "research article / experimental study": "writing_research_article",
    "学位论文": "writing_thesis",
    "thesis": "writing_thesis",
    "dissertation": "writing_thesis",
    "thesis / dissertation": "writing_thesis",
    "开题报告": "writing_proposal",
    "research proposal": "writing_proposal",
    "基金申请": "writing_grant",
    "grant proposal": "writing_grant",
    "调研报告": "writing_report",
    "research report": "writing_report",
    "自定义": "writing_custom",
    "custom": "writing_custom",
}

ICONS = {
    "print": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/></svg>',
    "arrow": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg>',
    "target": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/></svg>',
    "code": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m8 7-5 5 5 5"/><path d="m16 7 5 5-5 5"/></svg>',
    "list": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3.5 6h.01"/><path d="M3.5 12h.01"/><path d="M3.5 18h.01"/></svg>',
    "book": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
    "globe": '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18"/><path d="M12 3a14 14 0 0 0 0 18"/></svg>',
}

CSS = r"""
:root{color-scheme:light;--bg:#f6f8fa;--surface:#fff;--ink:#17212b;--muted:#5f6d78;--line:#d9e1e7;--line-strong:#bcc9d2;--navy:#1f506c;--navy-deep:#17394f;--teal:#18766f;--teal-soft:#e5f1f0;--link:#096d87;--green:#2e7d4f;--green-soft:#e8f3eb;--amber:#a76516;--amber-soft:#f8efdf;--red:#b54747;--red-soft:#f8e8e8;--soft:#eef3f5;--mono:Consolas,"Cascadia Mono","Courier New",monospace;--sans:"Microsoft YaHei","Noto Sans CJK SC","Segoe UI",Arial,sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--ink);background:var(--bg);font:15px/1.68 var(--sans);letter-spacing:0}
a{color:var(--link);text-underline-offset:3px}button,input,select{font:inherit;letter-spacing:0}:focus-visible{outline:2px solid var(--teal);outline-offset:2px}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}.skip-link{position:absolute;left:-9999px;top:10px;z-index:100;padding:9px 14px;color:var(--navy-deep);background:var(--surface);border:2px solid var(--teal);border-radius:6px;text-decoration:none}.skip-link:focus{left:12px}
.icon{width:18px;height:18px;flex:0 0 18px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.topbar{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:22px;min-height:58px;padding:0 26px;background:rgba(255,255,255,.97);border-bottom:1px solid var(--line)}
.brand{display:inline-flex;align-items:center;gap:9px;color:var(--ink);text-decoration:none;font-weight:700}.brand-mark{width:28px;height:28px;display:grid;place-items:center;color:#fff;background:var(--navy);border-radius:6px;font:700 12px/1 var(--sans)}.brand-name{white-space:nowrap}.project-context{flex:1;min-width:90px;color:var(--muted);font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;border-left:1px solid var(--line);padding-left:18px}
.primary-nav{display:flex;align-items:center;justify-content:flex-end;gap:3px;min-width:0;overflow-x:auto;scrollbar-width:none}.primary-nav::-webkit-scrollbar{display:none}.primary-nav a{padding:8px 11px;color:var(--muted);text-decoration:none;border-radius:5px;white-space:nowrap}.primary-nav a:hover{color:var(--ink);background:var(--soft)}.primary-nav a[aria-current=page]{color:var(--navy);background:#e7eff3;font-weight:700}
.header-tools{display:flex;align-items:center;gap:6px}.icon-button,.language-button{display:inline-flex;align-items:center;justify-content:center;height:36px;color:var(--muted);background:transparent;border:1px solid transparent;border-radius:5px;cursor:pointer}.icon-button{width:36px;padding:0}.language-button{gap:6px;min-width:68px;padding:0 9px;font-size:12px;font-weight:700}.icon-button:hover,.language-button:hover{color:var(--navy);background:var(--soft);border-color:var(--line)}.language-button .icon{width:16px;height:16px;flex-basis:16px}.language-code{min-width:22px;text-align:center}
.page-layout{display:grid;grid-template-columns:210px minmax(0,920px);gap:42px;max-width:1220px;margin:0 auto;padding:36px 30px 76px}.page-layout.no-toc{grid-template-columns:minmax(0,920px);max-width:980px}.toc-inner{position:sticky;top:88px;padding:13px 0}.toc-title{margin:0 0 10px;color:var(--muted);font-size:12px;font-weight:700}.toc nav{display:grid;gap:2px;border-left:1px solid var(--line)}.toc a{display:block;margin-left:-1px;padding:6px 10px;color:var(--muted);text-decoration:none;line-height:1.42;border-left:2px solid transparent}.toc a.sub{padding-left:22px;font-size:13px}.toc a:hover{color:var(--navy);border-left-color:var(--teal)}
.document{min-width:0;padding:30px 34px 42px;background:var(--surface);border:1px solid var(--line);border-radius:8px}.document>h1:first-of-type{margin-top:0}.doc-kicker{margin:0 0 7px;color:var(--teal);font-size:12px;font-weight:700}.page-status{display:flex;align-items:center;gap:10px;margin:-10px 0 24px;padding:10px 12px;background:var(--soft);border:1px solid var(--line);border-radius:6px;color:var(--muted);font-size:13px}.page-status strong{color:var(--ink)}
h1,h2,h3,h4{color:var(--navy-deep);line-height:1.32;overflow-wrap:anywhere;letter-spacing:0}h1{margin:0 0 22px;padding-bottom:13px;border-bottom:2px solid var(--navy);font-size:29px}h2{margin:38px 0 14px;padding-bottom:7px;border-bottom:1px solid var(--line);font-size:20px}h3{margin:25px 0 10px;color:var(--ink);font-size:16px}p{max-width:76ch;margin:10px 0 16px}ul,ol{margin:10px 0 18px;padding-left:24px}li{margin:5px 0}hr{margin:32px 0;border:0;border-top:1px solid var(--line)}
code{font-family:var(--mono);font-size:.92em;color:#17394f;background:#edf2f4;padding:2px 5px;border-radius:3px;overflow-wrap:anywhere}.code-shell{margin:13px 0 22px;background:var(--surface);border:1px solid var(--line-strong);border-radius:6px;overflow:hidden}.code-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:42px;padding:6px 8px 6px 13px;background:#f3f6f7;border-bottom:1px solid var(--line)}.code-label{min-width:0;color:var(--muted);font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}pre{min-height:64px;margin:0;overflow:auto;padding:16px;color:#16313f;background:#fbfcfc;border-left:3px solid var(--teal);font:12.5px/1.65 var(--mono);white-space:pre}pre code{display:block;min-width:max-content;padding:0;color:inherit;background:transparent;white-space:pre;overflow-wrap:normal}.copy-button{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-width:80px;height:30px;padding:0 10px;color:#fff;background:var(--teal);border:0;border-radius:5px;cursor:pointer;font-size:12px;font-weight:700}.copy-button:hover{background:#115f5a}.copy-button:active{transform:scale(.98)}.copy-button.copied{background:var(--green)}
blockquote,.doc-note{margin:18px 0;padding:12px 15px;color:#3f4f59;background:#edf5f4;border-left:3px solid var(--teal);border-radius:0 6px 6px 0}.table-wrap{width:100%;overflow:auto;margin:16px 0 24px;background:var(--surface);border:1px solid var(--line);border-radius:6px}table{width:100%;min-width:680px;border-collapse:collapse}th,td{padding:9px 11px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);overflow-wrap:anywhere}th{position:sticky;top:0;z-index:2;color:#29485d;background:#eaf0f3;font-size:13px;font-weight:700}tbody tr:last-child td{border-bottom:0}tbody tr:nth-child(even){background:#f8fafb}tbody tr:hover{background:#edf6f5}
.status-badge{display:inline-flex;align-items:center;gap:5px;padding:2px 7px;border:1px solid transparent;border-radius:4px;font-size:12px;font-weight:700;white-space:nowrap}.status-badge::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}.status-pass,.status-verified{color:var(--green);background:var(--green-soft);border-color:#bddbc6}.status-warning,.status-pending{color:var(--amber);background:var(--amber-soft);border-color:#ead2a8}.status-fail,.status-dropped{color:var(--red);background:var(--red-soft);border-color:#ebc2c2}.status-oa{color:var(--teal);background:var(--teal-soft);border-color:#b9d9d6}.status-neutral,.status-closed{color:var(--muted);background:var(--soft);border-color:var(--line)}
.tabs,.variant-tabs{display:flex;width:100%;overflow-x:auto;scrollbar-width:none;scroll-snap-type:x proximity}.tabs::-webkit-scrollbar,.variant-tabs::-webkit-scrollbar{display:none}.tabs{gap:4px;margin:18px 0 20px;border-bottom:1px solid var(--line)}.tab-button{flex:0 0 auto;min-height:40px;padding:8px 12px;color:var(--muted);background:transparent;border:0;border-bottom:2px solid transparent;cursor:pointer;font-size:13.5px;scroll-snap-align:start}.tab-button:hover{color:var(--ink);background:var(--soft)}.tab-button.active{color:var(--navy);border-bottom-color:var(--teal);font-weight:700}.platform-panel[hidden],.query-variant-panel[hidden]{display:none}.platform-panel>h2:first-child{margin-top:0}.variant-tabs{gap:6px;margin:12px 0 16px;padding:5px;background:var(--soft);border:1px solid var(--line);border-radius:6px}.variant-button{flex:0 0 auto;min-height:34px;padding:6px 10px;color:var(--muted);background:transparent;border:1px solid transparent;border-radius:4px;cursor:pointer;font-size:12.5px}.variant-button:hover{color:var(--ink)}.variant-button.active{color:var(--navy);background:var(--surface);border-color:var(--line-strong);font-weight:700}.variant-button[data-recommended=true]::after{content:" " attr(data-recommended-label);color:var(--teal);font-size:11px}.query-variant-panel>h3:first-child{margin-top:14px}
[data-page=candidate_list] table{min-width:1140px;font-size:13.5px;table-layout:fixed}[data-page=candidate_list] .candidate-col-id{width:52px;min-width:52px;text-align:center;white-space:nowrap}[data-page=candidate_list] .candidate-col-title{width:33%;min-width:340px}[data-page=candidate_list] .candidate-col-author{width:16%;min-width:165px}[data-page=candidate_list] .candidate-col-year{width:68px;min-width:68px;text-align:center;white-space:nowrap}[data-page=candidate_list] .candidate-col-doi{width:18%;min-width:185px;font-size:12.5px}[data-page=candidate_list] .candidate-col-verification{width:124px;min-width:124px;white-space:nowrap}[data-page=candidate_list] .candidate-col-oa{width:132px;min-width:132px;white-space:nowrap}.data-tools{position:sticky;top:58px;z-index:12;margin:16px 0 20px;padding:15px;background:rgba(255,255,255,.98);border:1px solid var(--line);border-radius:7px}.metric-strip{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:1px;margin-bottom:14px;background:var(--line);border:1px solid var(--line);border-radius:5px;overflow:hidden}.metric{min-width:0;padding:9px 11px;background:var(--surface)}.metric span{display:block;color:var(--muted);font-size:11.5px}.metric strong{display:block;margin-top:2px;color:var(--navy-deep);font-size:20px}.filter-row{display:grid;grid-template-columns:minmax(210px,1fr) 145px 125px 96px 96px;gap:8px}.field{display:grid;gap:4px;min-width:0}.field label{color:var(--muted);font-size:11.5px;font-weight:700}.field input,.field select{width:100%;height:37px;min-width:0;padding:6px 9px;color:var(--ink);background:var(--surface);border:1px solid var(--line-strong);border-radius:5px}.filter-footer{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:10px}.result-count{margin:0;color:var(--muted);font-size:12.5px}.filter-actions{display:flex;gap:6px}.command-button{display:inline-flex;align-items:center;gap:6px;min-height:32px;padding:5px 9px;color:var(--navy);background:var(--surface);border:1px solid var(--line-strong);border-radius:5px;cursor:pointer;font-size:12px}.command-button:hover{color:var(--teal);border-color:#8dbab6;background:#f1f8f7}.command-button.active{color:#fff;background:var(--teal);border-color:var(--teal)}.sort-button{width:100%;padding:0;text-align:left;color:inherit;background:transparent;border:0;cursor:pointer;font-weight:inherit}.sort-button[data-direction=asc]::after{content:"  ↑";color:var(--teal)}.sort-button[data-direction=desc]::after{content:"  ↓";color:var(--teal)}.empty-state{margin:12px 0;padding:22px;text-align:center;color:var(--muted);background:var(--soft);border:1px dashed var(--line-strong);border-radius:6px}
.document-language-panel[hidden]{display:none}.document-language-panel>h1:first-child{margin-top:0}.scope-statement{margin:12px 0 24px;padding:16px 18px;background:#f4f8f8;border:1px solid var(--line);border-left:3px solid var(--teal);border-radius:0 6px 6px 0;font-size:15.5px}.tier-list,.exclusion-list{list-style:none;padding:0;margin:12px 0 20px;display:grid;gap:8px}.tier-list li,.exclusion-list li{margin:0;padding:10px 12px;background:var(--surface);border:1px solid var(--line);border-radius:5px}.tier-list li{display:flex;gap:10px;align-items:flex-start}.tier-chip{flex:0 0 auto;margin-top:1px;padding:2px 7px;color:var(--teal);background:var(--teal-soft);border:1px solid #c5dfdc;border-radius:4px;font-size:11px;font-weight:700}.exclusion-list{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px 12px}.exclusion-list li{display:flex;align-items:center;gap:8px;color:#4a5963;font-size:13.5px}.exclusion-mark{color:var(--red);font-weight:700}.priority-text{padding:12px 14px;background:var(--soft);border-left:3px solid var(--navy);border-radius:0 5px 5px 0}
.home-main{max-width:1120px;margin:0 auto;padding:48px 30px 72px}.home-hero{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(280px,.75fr);gap:42px;align-items:start}.home-kicker{margin:0 0 9px;color:var(--teal);font-size:12px;font-weight:700}.home-main h1{max-width:840px;margin:0 0 12px;padding:0;border:0;color:var(--navy-deep);font-size:32px}.home-lead{max-width:70ch;color:var(--muted);font-size:16px}.meta-line{display:flex;flex-wrap:wrap;gap:8px 28px;margin-top:20px;padding:11px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);color:var(--muted);font-size:12.5px}.meta-line b{color:var(--ink)}.overview-panel{padding:17px 18px;background:var(--surface);border:1px solid var(--line);border-radius:7px}.overview-panel h2{margin:0 0 8px;padding:0;border:0;color:var(--muted);font-size:13px}.overview-row{display:flex;justify-content:space-between;gap:16px;padding:9px 0;border-top:1px solid var(--line);font-size:13px}.overview-row:first-of-type{border-top:0}.overview-row span{color:var(--muted)}.overview-row strong{text-align:right;color:var(--ink)}
.pipeline{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:32px 0 26px}.step{display:grid;grid-template-columns:auto 1fr;gap:10px 11px;min-height:126px;padding:16px;color:var(--ink);text-decoration:none;background:var(--surface);border:1px solid var(--line);border-radius:7px}.step:hover{border-color:#8dbab6;background:#f7fbfa}.step-icon{display:grid;place-items:center;width:30px;height:30px;color:var(--teal);background:var(--teal-soft);border-radius:5px}.step-icon .icon{width:17px;height:17px}.step-copy{min-width:0}.step-number{display:block;color:var(--muted);font-size:11px}.step-title{display:block;margin-top:2px;color:var(--navy-deep);font-size:15px;font-weight:700}.step-desc{grid-column:1/-1;display:block;color:var(--muted);font-size:12.5px}.home-note{margin-top:22px;padding:12px 15px;color:#3f4f59;background:#edf5f4;border-left:3px solid var(--teal);border-radius:0 6px 6px 0}.site-footer{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px 20px;max-width:1120px;margin:34px auto 0;padding:16px 30px 24px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}.home-main>.site-footer{max-width:none;margin-top:34px;padding:16px 0 0}.noscript{padding:9px 15px;color:#6b4a14;background:#faf3e0;border-bottom:1px solid #e8d9a8;font-size:13px}
@media(max-width:1000px){.topbar{padding:0 16px}.project-context{display:none}.primary-nav{margin-left:auto}.page-layout,.page-layout.no-toc{grid-template-columns:1fr;padding:28px 22px 58px}.toc{display:none}.home-hero{grid-template-columns:1fr;gap:24px}.pipeline{grid-template-columns:repeat(2,1fr)}.filter-row{grid-template-columns:minmax(180px,1fr) repeat(2,130px)}.filter-row .field:nth-child(4),.filter-row .field:nth-child(5){grid-row:2}}
@media(max-width:700px){.topbar{flex-wrap:wrap;gap:8px;min-height:54px;padding:8px 13px}.brand{flex:1}.primary-nav{justify-content:flex-start;order:3;width:100%;margin-left:0;padding-top:2px}.brand-name{font-size:14px}.page-layout,.home-main{padding:22px 14px 48px}.document{padding:22px 16px 32px}h1{font-size:25px}h2{font-size:19px}.home-main h1{font-size:27px}.pipeline{grid-template-columns:1fr}.metric-strip{grid-template-columns:repeat(2,1fr)}.metric:last-child{grid-column:1/-1}.filter-row{grid-template-columns:1fr 1fr}.filter-row .field:first-child{grid-column:1/-1}.filter-row .field:nth-child(4),.filter-row .field:nth-child(5){grid-row:auto}.filter-footer{align-items:flex-start;flex-direction:column}.exclusion-list{grid-template-columns:1fr}.data-tools{position:static;padding:12px}.variant-tabs{margin-left:0;margin-right:0}.site-footer{padding-left:14px;padding-right:14px}
[data-page=candidate_list] .table-wrap{overflow:visible;background:transparent;border:0}[data-page=candidate_list] table.mobile-ready,[data-page=candidate_list] table.mobile-ready tbody,[data-page=candidate_list] table.mobile-ready tr,[data-page=candidate_list] table.mobile-ready td{display:block;width:100%;min-width:0}[data-page=candidate_list] table.mobile-ready thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}[data-page=candidate_list] table.mobile-ready tbody{display:grid;gap:10px}[data-page=candidate_list] table.mobile-ready tr{padding:10px 12px;background:var(--surface);border:1px solid var(--line);border-radius:6px}[data-page=candidate_list] table.mobile-ready td{display:grid;grid-template-columns:92px minmax(0,1fr);gap:8px;padding:7px 0;border-bottom:1px solid var(--line);white-space:normal}[data-page=candidate_list] table.mobile-ready td:last-child{border-bottom:0}[data-page=candidate_list] table.mobile-ready td::before{content:attr(data-label);color:var(--muted);font-size:11.5px;font-weight:700}
}
@media print{.topbar,.toc,.tabs,.variant-tabs,.copy-button,.data-tools,.noscript,.site-footer,.skip-link,.overview-panel{display:none!important}body{color:#000;background:#fff;font-size:11pt}.page-layout{display:block;max-width:none;padding:0}.document{width:100%;padding:0;border:0}.document h1{color:#000;border-color:#777}.query-variant-panel[hidden],.platform-panel[hidden]{display:block}.code-toolbar{display:none}pre{white-space:pre-wrap;break-inside:avoid;background:#f6f6f6;color:#111;border:1px solid #ccc}.table-wrap{overflow:visible;border:0}table{min-width:0;font-size:9pt}th{background:#eee}a{color:#000;text-decoration:none}.home-main{max-width:none;padding:0}.pipeline{grid-template-columns:repeat(2,1fr)}.step,.scope-statement,.tier-list li,.exclusion-list li,.home-note{background:#fff;color:#111;border-color:#bbb}}
"""

JS = r"""
(function(){'use strict';
const copyIcon='<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>';
const checkIcon='<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m20 6-11 11-5-5"/></svg>';
const I18N={
zh:{
page_index_title:'检索策略包',page_scope_card_title:'研究范围',page_query_pack_title:'六库检索式合集',page_candidate_list_title:'候选文献清单',page_usage_guide_title:'检索使用说明',
skip_main:'跳到主要内容',nav_overview:'总览',nav_scope_card:'范围卡',nav_query_pack:'检索式',nav_candidate_list:'候选文献',nav_usage_guide:'使用说明',primary_nav:'主要导航',print_page:'打印本页',switch_english:'切换为英文界面',switch_chinese:'切换为中文界面',
toc_aria:'本页目录',toc_title:'本页目录',noscript:'交互增强未启用，全部文档内容仍可正常阅读。',offline_package:'QueryStrategist · 离线检索策略包',citation_warning:'候选文献需人工核验后方可引用',local_files:'本地自包含文件，无需联网',
home_kicker:'QUERYSTRATEGIST / 离线检索工作台',home_lead:'从研究范围确认、检索式执行到候选文献筛选，所有内容均可离线浏览和复制。',generated_date:'生成日期',writing_type:'写作类型',writing_review:'综述',writing_research_article:'研究论著/实验研究',writing_thesis:'学位论文',writing_proposal:'开题报告',writing_grant:'基金申请',writing_report:'调研报告',writing_custom:'自定义',time_span:'时间范围',result_summary:'结果摘要',query_count:'检索式',candidate_count:'候选文献',doi_verified:'DOI 已验证',open_access:'开放获取',query_unit:'条',record_unit:'篇',qa_label:'Query QA',pipeline_aria:'策略包阅读流程',step:'步骤 {number}',home_note:'建议先确认研究范围，再使用推荐起步检索式。候选文献仅供筛选，正式引用前仍需核验题名、作者、年份、DOI 与全文内容。',
scope_title:'研究范围',scope_desc:'确认对象、技术、任务、排除项与检索边界。',queries_title:'六库检索式合集',queries_desc:'按数据库查看、复制并验证检索式。',candidates_title:'候选文献清单',candidates_desc:'搜索、筛选和排序 API 收割的待核验文献。',guide_title:'检索使用说明',guide_desc:'查看各平台填入位置以及调宽、调窄方法。',
query_document_title:'六库检索式合集',candidate_document_title:'候选文献清单',query_usage:'使用方式：请在数据库界面中设置 {timeSpan} 年份筛选（如平台支持）。',database_tabs:'数据库',variant_tabs:'检索式层级',variant_a0:'A0 高召回基线',variant_a1:'A1 主题检索',variant_b:'B 精准检索',variant_review_oriented:'E 综述导向',variant_review:'综述检索',recommended:'推荐',query_fallback:'检索式 {number}',copy_query:'复制检索式',copy:'复制',copied:'已复制',copy_failed:'复制失败',qa_notice:'最终仍以数据库官网解析和命中结果为准。',document_fallback:'检索策略包',
total_candidates:'候选总数',verified:'已验证',pending:'待人工核验',dropped:'已剔除',unknown:'未知',not_open_access:'非开放获取',search_label:'标题、作者或 DOI',search_placeholder:'搜索候选文献',verification_status:'验证状态',oa_status:'OA 状态',all:'全部',start_year:'起始年份',end_year:'截止年份',verified_only:'仅看已验证',clear_filters:'清除筛选',empty_candidates:'没有符合当前筛选条件的候选文献。',showing_count:'当前显示 {visible} / {total} 条',sort_by:'按{label}排序',field:'字段',
header_no:'序号',header_title:'题名',header_first_author:'第一作者',header_authors:'作者',header_year:'年份',header_source:'来源',header_doi:'DOI',header_status:'核验状态',header_oa:'开放获取状态',header_abstract:'摘要',header_keywords:'关键词'
},
en:{
page_index_title:'Search Strategy Package',page_scope_card_title:'Research Scope',page_query_pack_title:'Multi-Database Query Pack',page_candidate_list_title:'Candidate Literature List',page_usage_guide_title:'Search Guide',
skip_main:'Skip to main content',nav_overview:'Overview',nav_scope_card:'Scope Card',nav_query_pack:'Query Pack',nav_candidate_list:'Candidate List',nav_usage_guide:'Guide',primary_nav:'Primary navigation',print_page:'Print this page',switch_english:'Switch interface to English',switch_chinese:'Switch interface to Chinese',
toc_aria:'On this page',toc_title:'On this page',noscript:'Interactive enhancements are disabled. All document content remains readable.',offline_package:'QueryStrategist · Offline Search Strategy Package',citation_warning:'Verify candidate records manually before citing',local_files:'Self-contained local files · No internet required',
home_kicker:'QUERYSTRATEGIST / OFFLINE SEARCH WORKBENCH',home_lead:'Review the research scope, run database queries, and screen candidate records in one offline workspace.',generated_date:'Generated',writing_type:'Writing type',writing_review:'Review',writing_research_article:'Research Article',writing_thesis:'Thesis / Dissertation',writing_proposal:'Research Proposal',writing_grant:'Grant Proposal',writing_report:'Research Report',writing_custom:'Custom',time_span:'Time span',result_summary:'Result Summary',query_count:'Queries',candidate_count:'Candidates',doi_verified:'DOI Verified',open_access:'Open Access',query_unit:'queries',record_unit:'records',qa_label:'Query QA',pipeline_aria:'Package workflow',step:'Step {number}',home_note:'Confirm the research scope first, then begin with the recommended query. Candidate records are provided for screening only; verify the title, authors, year, DOI, and full text before citing.',
scope_title:'Research Scope',scope_desc:'Confirm the subject, methods, tasks, exclusions, and search boundaries.',queries_title:'Multi-Database Query Pack',queries_desc:'Review, copy, and validate queries by database.',candidates_title:'Candidate Literature List',candidates_desc:'Search, filter, and sort API-harvested records awaiting verification.',guide_title:'Search Guide',guide_desc:'See where to paste each query and how to broaden or narrow it.',
query_document_title:'Multi-Database Query Pack',candidate_document_title:'Candidate Literature List',query_usage:'Usage: apply the {timeSpan} year filter in the database UI where supported.',database_tabs:'Databases',variant_tabs:'Query levels',variant_a0:'A0 Recall Baseline',variant_a1:'A1 Topical Search',variant_b:'B Precision Search',variant_review_oriented:'E Review-Oriented',variant_review:'Review Search',recommended:'Recommended',query_fallback:'Query {number}',copy_query:'Copy query',copy:'Copy',copied:'Copied',copy_failed:'Copy failed',qa_notice:'Always confirm parsing and result counts on the official database website.',document_fallback:'Search Strategy Package',
total_candidates:'Total Candidates',verified:'Verified',pending:'Manual Review',dropped:'Excluded',unknown:'Unknown',not_open_access:'Not Open Access',search_label:'Title, author, or DOI',search_placeholder:'Search candidate records',verification_status:'Verification Status',oa_status:'OA Status',all:'All',start_year:'Start Year',end_year:'End Year',verified_only:'Verified Only',clear_filters:'Clear Filters',empty_candidates:'No candidate records match the current filters.',showing_count:'Showing {visible} of {total} records',sort_by:'Sort by {label}',field:'Field',
header_no:'No.',header_title:'Title',header_first_author:'First Author',header_authors:'Authors',header_year:'Year',header_source:'Source',header_doi:'DOI',header_status:'Verification Status',header_oa:'OA Status',header_abstract:'Abstract',header_keywords:'Keywords'
}};
function initialLanguage(){const requested=new URLSearchParams(window.location.search).get('lang');if(requested==='en'||requested==='zh')return requested;try{const saved=localStorage.getItem('qs-interface-language');if(saved==='en'||saved==='zh')return saved}catch(error){}return'zh'}
let currentLanguage=initialLanguage();
function t(key,values={}){const template=I18N[currentLanguage][key]||I18N.zh[key]||key;return template.replace(/\{(\w+)\}/g,(match,name)=>values[name]??match)}
function pageNavKey(page){return{scope_card:'nav_scope_card',query_pack:'nav_query_pack',candidate_list:'nav_candidate_list',usage_guide:'nav_usage_guide'}[page]||'document_fallback'}
function translateMarkedElements(){document.querySelectorAll('[data-i18n]').forEach(element=>{element.textContent=t(element.dataset.i18n,{number:element.dataset.number,timeSpan:element.dataset.timeSpan})});document.querySelectorAll('[data-i18n-title]').forEach(element=>{element.title=t(element.dataset.i18nTitle)});document.querySelectorAll('[data-i18n-aria-label]').forEach(element=>{element.setAttribute('aria-label',t(element.dataset.i18nAriaLabel))});document.querySelectorAll('[data-i18n-placeholder]').forEach(element=>{element.placeholder=t(element.dataset.i18nPlaceholder)})}
function updateBilingualContent(){document.querySelectorAll('.document').forEach(article=>{const panels=Array.from(article.querySelectorAll(':scope>.document-language-panel'));if(!panels.length)return;const target=panels.find(panel=>panel.dataset.contentLang===currentLanguage)||panels.find(panel=>panel.dataset.contentSource==='true')||panels[0];panels.forEach(panel=>{panel.hidden=panel!==target})})}
function updateLanguageLinks(){document.querySelectorAll('a[href]').forEach(link=>{const raw=link.getAttribute('href');if(!/^[^:#?]+\.html(?:[?#].*)?$/i.test(raw||''))return;const url=new URL(raw,window.location.href);if(currentLanguage==='en')url.searchParams.set('lang','en');else url.searchParams.delete('lang');link.setAttribute('href',url.pathname.slice(url.pathname.lastIndexOf('/')+1)+url.search+url.hash)})}
function variantKey(text){const value=text.trim();if(/^A0\b/i.test(value))return'variant_a0';if(/^A1\b/i.test(value))return'variant_a1';if(/^B\b/i.test(value))return'variant_b';if(/^E\b/i.test(value))return'variant_review_oriented';if(/review|综述/i.test(value))return'variant_review';return''}
function updateVariantLabels(){document.querySelectorAll('.variant-button').forEach(button=>{if(button.dataset.variantKey)button.textContent=t(button.dataset.variantKey);if(button.dataset.recommended==='true')button.dataset.recommendedLabel=t('recommended')})}
function updateCopyButtons(){document.querySelectorAll('.copy-button').forEach(button=>{const state=button.dataset.copyState||'copy';const key=state==='copied'?'copied':state==='failed'?'copy_failed':'copy';button.title=t('copy_query');button.setAttribute('aria-label',t('copy_query'));const label=button.querySelector('span');if(label)label.textContent=t(key)})}
function headerKey(value){const text=value.trim().toLowerCase();if(/^(no\.?|id|序号|编号)$/.test(text))return'header_no';if(/first author|第一作者/.test(text))return'header_first_author';if(/^(title|题名|标题)$/.test(text))return'header_title';if(/author|作者/.test(text))return'header_authors';if(/^(year|年份|年)$/.test(text))return'header_year';if(/journal|source|venue|期刊|来源/.test(text))return'header_source';if(/^doi$/.test(text))return'header_doi';if(/^oa\b|open access|开放获取/.test(text))return'header_oa';if(/verification|status|验证|状态|核验/.test(text))return'header_status';if(/abstract|摘要/.test(text))return'header_abstract';if(/keyword|关键词/.test(text))return'header_keywords';return''}
function markTranslatableDocuments(){const query=document.querySelector('[data-page="query_pack"]');if(query){const h1=query.querySelector(':scope>h1');if(h1)h1.dataset.i18n='query_document_title';Array.from(query.querySelectorAll(':scope>h3')).forEach(head=>{const key=variantKey(head.textContent);if(key)head.dataset.i18n=key});Array.from(query.querySelectorAll(':scope>p')).forEach(paragraph=>{const text=paragraph.textContent.trim(),span=text.match(/\b(\d{4}\s*[-–—]\s*\d{4})\b/);if(span&&(/usage/i.test(text)||/使用/.test(text))&&(/filter/i.test(text)||/筛选/.test(text))){paragraph.dataset.i18n='query_usage';paragraph.dataset.timeSpan=span[1]}})}const candidates=document.querySelector('[data-page="candidate_list"]');if(candidates){const h1=candidates.querySelector(':scope>h1');if(h1)h1.dataset.i18n='candidate_document_title'}}
document.addEventListener('DOMContentLoaded',markTranslatableDocuments);
function updateQueryLabels(){document.querySelectorAll('.code-label').forEach(label=>{const key=label.dataset.variantKey||variantKey(label.textContent);if(key){label.dataset.variantKey=key;label.textContent=t(key)}})}
document.addEventListener('DOMContentLoaded',()=>window.addEventListener('qs:languagechange',updateQueryLabels));
function candidateColumnClass(value){const text=value.trim().toLowerCase();if(/^(no\.?|id|序号|编号)$/.test(text))return'candidate-col-id';if(/^(title|题名|标题)$/.test(text))return'candidate-col-title';if(/author|作者/.test(text))return'candidate-col-author';if(/^(year|年份|年)$/.test(text))return'candidate-col-year';if(/^doi$/.test(text))return'candidate-col-doi';if(/verification|验证|核验/.test(text))return'candidate-col-verification';if(/^oa\b|open access|开放获取/.test(text))return'candidate-col-oa';return''}
function candidateColumnLayout(){const table=document.querySelector('[data-page="candidate_list"] table');if(!table)return;const headers=Array.from(table.tHead?.rows[0]?.cells||[]);const rows=Array.from(table.tBodies[0]?.rows||[]);headers.forEach((header,index)=>{const columnClass=candidateColumnClass(header.textContent);if(!columnClass)return;header.classList.add(columnClass);rows.forEach(row=>row.cells[index]?.classList.add(columnClass))})}
document.addEventListener('DOMContentLoaded',candidateColumnLayout);
function updateCandidateInterface(){document.querySelectorAll('[data-status-value]').forEach(badge=>{const key=badge.dataset.statusValue;badge.textContent=t(key)});document.querySelectorAll('.sort-button').forEach(button=>{const label=button.dataset.headerKey?t(button.dataset.headerKey):button.dataset.originalLabel;button.textContent=label;button.title=t('sort_by',{label});const column=Number(button.dataset.column);document.querySelectorAll('[data-page="candidate_list"] tbody tr').forEach(row=>{if(row.cells[column])row.cells[column].dataset.label=label})})}
function updateDocumentKicker(){const kicker=document.querySelector('.doc-kicker [data-page-label]');if(kicker)kicker.textContent=t(pageNavKey(kicker.dataset.pageLabel))}
function applyLanguage(language){currentLanguage=language==='en'?'en':'zh';document.documentElement.lang=currentLanguage==='en'?'en':'zh-CN';try{localStorage.setItem('qs-interface-language',currentLanguage)}catch(error){}updateBilingualContent();translateMarkedElements();updateVariantLabels();updateCopyButtons();updateCandidateInterface();updateDocumentKicker();updateLanguageLinks();const button=document.querySelector('#language-toggle');if(button){const key=currentLanguage==='zh'?'switch_english':'switch_chinese';button.title=t(key);button.setAttribute('aria-label',t(key));button.querySelector('.language-code').textContent=currentLanguage==='zh'?'EN':'中'}const titleKey=document.body.dataset.titleKey||'page_index_title';document.title=t(titleKey)+' | QueryStrategist';window.dispatchEvent(new CustomEvent('qs:languagechange',{detail:{language:currentLanguage}}))}
function slug(text,index){return text.trim().toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]+/g,'-').replace(/^-|-$/g,'')||'section-'+index}
function links(){document.querySelectorAll('a[href^="http"]').forEach(a=>{a.target='_blank';a.rel='noopener noreferrer'})}
function setTabs(buttons,panels,active){buttons.forEach((button,index)=>{const selected=index===active;button.classList.toggle('active',selected);button.setAttribute('aria-selected',selected?'true':'false');button.tabIndex=selected?0:-1;panels[index].hidden=!selected})}
function tabKeyboard(event,buttons,panels){const index=buttons.indexOf(event.currentTarget);let next=index;if(event.key==='ArrowRight')next=(index+1)%buttons.length;else if(event.key==='ArrowLeft')next=(index-1+buttons.length)%buttons.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=buttons.length-1;else return;event.preventDefault();setTabs(buttons,panels,next);buttons[next].focus()}
function queryTabs(){const article=document.querySelector('[data-page="query_pack"]');if(!article)return;const pattern=/web of science|wos|scopus|ieee|google scholar|cnki|知网|万方|wanfang/i;const heads=Array.from(article.querySelectorAll(':scope>h2')).filter(h=>pattern.test(h.textContent));if(heads.length<2)return;const tabs=document.createElement('div');tabs.className='tabs';tabs.setAttribute('role','tablist');tabs.dataset.i18nAriaLabel='database_tabs';const panels=[];const buttons=[];heads.forEach((head,index)=>{const panel=document.createElement('section');panel.className='platform-panel';panel.id='platform-'+index;head.parentNode.insertBefore(panel,head);panel.appendChild(head);while(panel.nextSibling&&panel.nextSibling.tagName!=='H2'&&!panel.nextSibling.classList?.contains('platform-panel'))panel.appendChild(panel.nextSibling);panels.push(panel);const button=document.createElement('button');button.type='button';button.className='tab-button';button.setAttribute('role','tab');button.setAttribute('aria-controls',panel.id);button.textContent=head.textContent;button.onclick=()=>setTabs(buttons,panels,index);button.onkeydown=event=>tabKeyboard(event,buttons,panels);buttons.push(button);tabs.appendChild(button)});panels[0].parentNode.insertBefore(tabs,panels[0]);setTabs(buttons,panels,0)}
function queryVariants(){document.querySelectorAll('.platform-panel').forEach((platform,pIndex)=>{const heads=Array.from(platform.children).filter(node=>node.tagName==='H3');if(heads.length<2)return;const tabs=document.createElement('div');tabs.className='variant-tabs';tabs.setAttribute('role','tablist');tabs.dataset.i18nAriaLabel='variant_tabs';const panels=[];const buttons=[];heads.forEach((head,index)=>{const panel=document.createElement('section');panel.className='query-variant-panel';panel.id='variant-'+pIndex+'-'+index;head.parentNode.insertBefore(panel,head);panel.appendChild(head);while(panel.nextSibling&&panel.nextSibling.tagName!=='H3')panel.appendChild(panel.nextSibling);panels.push(panel);const button=document.createElement('button');button.type='button';button.className='variant-button';button.setAttribute('role','tab');button.setAttribute('aria-controls',panel.id);button.dataset.variantKey=variantKey(head.textContent);button.textContent=button.dataset.variantKey?t(button.dataset.variantKey):head.textContent;if(/^A1\b/i.test(head.textContent))button.dataset.recommended='true';button.onclick=()=>setTabs(buttons,panels,index);button.onkeydown=event=>tabKeyboard(event,buttons,panels);buttons.push(button);tabs.appendChild(button)});panels[0].parentNode.insertBefore(tabs,panels[0]);const preferred=heads.findIndex(head=>/^A1\b/i.test(head.textContent));setTabs(buttons,panels,preferred>=0?preferred:0)})}
function copyButtons(){document.querySelectorAll('pre').forEach((pre,index)=>{if(pre.closest('.code-shell'))return;const heading=pre.closest('.query-variant-panel')?.querySelector('h3')?.textContent||t('query_fallback',{number:index+1});const shell=document.createElement('div');shell.className='code-shell';pre.parentNode.insertBefore(shell,pre);const toolbar=document.createElement('div');toolbar.className='code-toolbar';const label=document.createElement('span');label.className='code-label';label.textContent=heading;const button=document.createElement('button');button.type='button';button.className='copy-button';button.dataset.copyState='copy';button.innerHTML=copyIcon+'<span>'+t('copy')+'</span>';button.onclick=async()=>{try{const value=pre.textContent;if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(value)}else{const area=document.createElement('textarea');area.value=value;area.style.cssText='position:fixed;opacity:0';document.body.appendChild(area);area.select();document.execCommand('copy');area.remove()}button.classList.add('copied');button.dataset.copyState='copied';button.innerHTML=checkIcon+'<span>'+t('copied')+'</span>';setTimeout(()=>{button.classList.remove('copied');button.dataset.copyState='copy';button.innerHTML=copyIcon+'<span>'+t('copy')+'</span>'},1600)}catch(error){button.dataset.copyState='failed';button.querySelector('span').textContent=t('copy_failed')}};toolbar.append(label,button);shell.append(toolbar,pre)})}
function queryStatus(){const article=document.querySelector('[data-page="query_pack"]');if(!article)return;const value=(article.dataset.qaStatus||'未标注').toUpperCase();const status=document.createElement('div');status.className='page-status';const cls=value==='PASS'?'status-pass':value==='WARNING'?'status-warning':value==='FAIL'?'status-fail':'status-neutral';status.innerHTML='<strong data-i18n="qa_label">'+t('qa_label')+'</strong><span class="status-badge '+cls+'">'+value+'</span><span data-i18n="qa_notice">'+t('qa_notice')+'</span>';const h1=article.querySelector('h1');if(h1)h1.insertAdjacentElement('afterend',status)}
function classifyStatus(text){const value=text.toLowerCase();if(value.includes('unverified')||value.includes('待人工')||value.includes('pending'))return'pending';if(value.includes('dropped')||value.includes('已剔除')||value.includes('reject'))return'dropped';if(value.includes('verified')||value.includes('已验证'))return'verified';return'unknown'}
function classifyOa(text){const value=text.toLowerCase();if(/非\s*-?\s*oa|non\s*-?\s*oa|not open access|closed|false/.test(value))return'closed';if(value.includes('oa')||/gold|green|hybrid|bronze|open/.test(value))return'open';return'unknown'}
function candidateTools(){const article=document.querySelector('[data-page="candidate_list"]');if(!article)return;const table=article.querySelector('table');if(!table||!table.tBodies.length)return;const rows=Array.from(table.tBodies[0].rows);const headerCells=Array.from(table.tHead?.rows[0]?.cells||[]);const headers=headerCells.map(cell=>cell.textContent.trim());const normalized=headers.map(value=>value.toLowerCase());const find=words=>normalized.findIndex(value=>words.some(word=>value.includes(word)));const yearCol=find(['year','年份','年']);const statusCol=normalized.findIndex(value=>(/verification|验证|核验/.test(value)||(/status|状态/.test(value)&&!/\boa\b|open access|开放获取/.test(value))));const oaCol=find(['oa','开放获取']);rows.forEach(row=>{row.dataset.status=classifyStatus(statusCol>=0?row.cells[statusCol]?.textContent:row.textContent);row.dataset.oa=classifyOa(oaCol>=0?row.cells[oaCol]?.textContent:row.textContent)});const status=row=>row.dataset.status||'unknown';const oa=row=>row.dataset.oa||'unknown';rows.forEach(row=>{Array.from(row.cells).forEach((cell,index)=>cell.dataset.label=headers[index]||t('field'));if(statusCol>=0){const cell=row.cells[statusCol],raw=cell.textContent.trim(),value=status(row);cell.textContent='';const badge=document.createElement('span');badge.className='status-badge status-'+(value==='unknown'?'neutral':value);if(value==='unknown')badge.textContent=raw||t('unknown');else{badge.dataset.statusValue=value;badge.textContent=t(value)}cell.appendChild(badge)}if(oaCol>=0){const cell=row.cells[oaCol],raw=cell.textContent.trim(),value=oa(row);cell.textContent='';const badge=document.createElement('span');badge.className='status-badge status-'+(value==='open'?'oa':value==='closed'?'closed':'neutral');if(value==='unknown')badge.textContent=raw||t('unknown');else{badge.dataset.statusValue=value==='open'?'open_access':'not_open_access';badge.textContent=t(badge.dataset.statusValue)}cell.appendChild(badge)}});table.classList.add('mobile-ready');const counts={verified:rows.filter(row=>status(row)==='verified').length,pending:rows.filter(row=>status(row)==='pending').length,dropped:rows.filter(row=>status(row)==='dropped').length,open:rows.filter(row=>oa(row)==='open').length};const tools=document.createElement('section');tools.className='data-tools';tools.innerHTML='<div class="metric-strip"><div class="metric"><span data-i18n="total_candidates"></span><strong>'+rows.length+'</strong></div><div class="metric"><span data-i18n="verified"></span><strong>'+counts.verified+'</strong></div><div class="metric"><span data-i18n="pending"></span><strong>'+counts.pending+'</strong></div><div class="metric"><span data-i18n="dropped"></span><strong>'+counts.dropped+'</strong></div><div class="metric"><span data-i18n="open_access"></span><strong>'+counts.open+'</strong></div></div><div class="filter-row"><div class="field"><label for="candidate-search" data-i18n="search_label"></label><input id="candidate-search" type="search" data-i18n-placeholder="search_placeholder"></div><div class="field"><label for="status-filter" data-i18n="verification_status"></label><select id="status-filter"><option value="" data-i18n="all"></option><option value="verified" data-i18n="verified"></option><option value="pending" data-i18n="pending"></option><option value="dropped" data-i18n="dropped"></option></select></div><div class="field"><label for="oa-filter" data-i18n="oa_status"></label><select id="oa-filter"><option value="" data-i18n="all"></option><option value="open" data-i18n="open_access"></option><option value="closed" data-i18n="not_open_access"></option><option value="unknown" data-i18n="unknown"></option></select></div><div class="field"><label for="year-min" data-i18n="start_year"></label><input id="year-min" type="number" placeholder="2016"></div><div class="field"><label for="year-max" data-i18n="end_year"></label><input id="year-max" type="number" placeholder="2026"></div></div><div class="filter-footer"><p class="result-count" aria-live="polite"></p><div class="filter-actions"><button id="verified-only" class="command-button" type="button" data-i18n="verified_only"></button><button id="clear-filters" class="command-button" type="button" data-i18n="clear_filters"></button></div></div>';const wrap=table.closest('.table-wrap');wrap.parentNode.insertBefore(tools,wrap);const empty=document.createElement('div');empty.className='empty-state';empty.hidden=true;empty.dataset.i18n='empty_candidates';wrap.insertAdjacentElement('afterend',empty);const search=tools.querySelector('#candidate-search'),statusFilter=tools.querySelector('#status-filter'),oaFilter=tools.querySelector('#oa-filter'),yearMin=tools.querySelector('#year-min'),yearMax=tools.querySelector('#year-max'),count=tools.querySelector('.result-count'),verifiedOnly=tools.querySelector('#verified-only');function filter(){const query=search.value.trim().toLowerCase(),min=Number(yearMin.value)||-Infinity,max=Number(yearMax.value)||Infinity;let visible=0;rows.forEach(row=>{const year=yearCol>=0?Number((row.cells[yearCol]?.textContent||'').match(/\d{4}/)?.[0]):0;const show=(!query||row.textContent.toLowerCase().includes(query))&&(!statusFilter.value||status(row)===statusFilter.value)&&(!oaFilter.value||oa(row)===oaFilter.value)&&(!year||(year>=min&&year<=max));row.hidden=!show;if(show)visible++});count.textContent=t('showing_count',{visible,total:rows.length});empty.hidden=visible!==0;verifiedOnly.classList.toggle('active',statusFilter.value==='verified')}[search,statusFilter,oaFilter,yearMin,yearMax].forEach(control=>control.addEventListener(control.tagName==='SELECT'?'change':'input',filter));verifiedOnly.onclick=()=>{statusFilter.value=statusFilter.value==='verified'?'':'verified';filter()};tools.querySelector('#clear-filters').onclick=()=>{search.value='';statusFilter.value='';oaFilter.value='';yearMin.value='';yearMax.value='';filter()};window.addEventListener('qs:languagechange',filter);headerCells.forEach((cell,column)=>{const original=cell.textContent.trim(),button=document.createElement('button');button.type='button';button.className='sort-button';button.dataset.column=column;button.dataset.originalLabel=original;const key=headerKey(original);if(key)button.dataset.headerKey=key;button.textContent=key?t(key):original;button.title=t('sort_by',{label:button.textContent});button.onclick=()=>{const direction=button.dataset.direction==='asc'?'desc':'asc';table.querySelectorAll('.sort-button').forEach(item=>delete item.dataset.direction);button.dataset.direction=direction;rows.sort((left,right)=>{const a=left.cells[column]?.textContent.trim()||'',b=right.cells[column]?.textContent.trim()||'';const an=Number(a.replace(/[^0-9.-]/g,'')),bn=Number(b.replace(/[^0-9.-]/g,''));const comparison=Number.isFinite(an)&&Number.isFinite(bn)&&a&&b?an-bn:a.localeCompare(b,currentLanguage==='zh'?'zh-CN':'en',{numeric:true});return direction==='asc'?comparison:-comparison});rows.forEach(row=>table.tBodies[0].appendChild(row))};cell.textContent='';cell.appendChild(button)});filter()}
function scopeEnhance(){const article=document.querySelector('[data-page="scope_card"]');if(!article)return;Array.from(article.querySelectorAll('h2')).forEach(head=>{const text=head.textContent.trim().toLowerCase();const next=head.nextElementSibling;if(/^(scope|research scope|研究范围|范围)$/.test(text)&&next?.tagName==='P')next.classList.add('scope-statement');if(/keyword tiers|关键词层级|关键词体系/.test(text)&&next?.tagName==='UL'){next.classList.add('tier-list');next.querySelectorAll('li').forEach(item=>{const raw=item.textContent.trim(),parts=raw.split(/:\s*/,2);if(parts.length===2){item.textContent='';const chip=document.createElement('span');chip.className='tier-chip';chip.textContent=parts[0];const value=document.createElement('span');value.textContent=parts[1];item.append(chip,value)}})}if(/exclusion|排除/.test(text)&&next?.tagName==='UL'){next.classList.add('exclusion-list');next.querySelectorAll('li').forEach(item=>{const mark=document.createElement('span');mark.className='exclusion-mark';mark.textContent='×';mark.setAttribute('aria-hidden','true');item.prepend(mark)})}if(/priority|优先级/.test(text)&&next?.tagName==='P')next.classList.add('priority-text')})}
function decorateDocument(){const article=document.querySelector('.document');if(!article||article.querySelector(':scope>.doc-kicker'))return;const kicker=document.createElement('p');kicker.className='doc-kicker';kicker.append('QUERYSTRATEGIST / ');const label=document.createElement('span');label.dataset.pageLabel=article.dataset.page;label.textContent=t(pageNavKey(article.dataset.page));kicker.appendChild(label);article.prepend(kicker)}
function toc(){const article=document.querySelector('.document'),nav=document.querySelector('#toc-nav');if(!article||!nav)return;nav.textContent='';const panel=article.querySelector(':scope>.document-language-panel:not([hidden])');const root=panel||article;const selector=article.dataset.page==='query_pack'?':scope>h2':':scope>h2,:scope>h3';const heads=Array.from(root.querySelectorAll(selector));const prefix=panel?.dataset.contentLang||'doc';heads.forEach((head,index)=>{if(!head.id)head.id=prefix+'-'+slug(head.textContent,index);const link=document.createElement('a');link.href='#'+head.id;link.textContent=head.textContent;if(head.tagName==='H3')link.className='sub';nav.appendChild(link)});const aside=nav.closest('.toc');if(aside)aside.hidden=!heads.length;document.querySelector('.page-layout')?.classList.toggle('no-toc',!heads.length)}
document.addEventListener('DOMContentLoaded',()=>{links();queryTabs();queryVariants();copyButtons();queryStatus();candidateTools();scopeEnhance();decorateDocument();const print=document.querySelector('#print-page');if(print)print.onclick=()=>window.print();const language=document.querySelector('#language-toggle');if(language)language.onclick=()=>applyLanguage(currentLanguage==='zh'?'en':'zh');window.addEventListener('qs:languagechange',toc);applyLanguage(currentLanguage)});})();
"""


def _navigation(active_page, available_pages):
    current = ' aria-current="page"' if active_page == "index" else ""
    links = [f'<a href="index.html" data-i18n="nav_overview"{current}>总览</a>']
    for key in available_pages:
        label = PAGE_META[key][0]
        i18n_key = PAGE_I18N[key][0]
        current = ' aria-current="page"' if active_page == key else ""
        links.append(
            f'<a href="{key}.html" data-i18n="{i18n_key}"{current}>{label}</a>'
        )
    return "".join(links)


def _status_badge(value):
    normalized = str(value or "未标注").upper()
    css_class = {
        "PASS": "status-pass",
        "WARNING": "status-warning",
        "FAIL": "status-fail",
    }.get(normalized, "status-neutral")
    return f'<span class="status-badge {css_class}">{html.escape(normalized)}</span>'


def _writing_type_markup(value):
    text = str(value or "未记录").strip()
    i18n_key = WRITING_TYPE_I18N.get(" ".join(text.casefold().split()))
    attribute = f' data-i18n="{i18n_key}"' if i18n_key else ""
    return f"<b{attribute}>{html.escape(text)}</b>"


def shell(title, content, page_key, available_pages, home=False, summary=None):
    summary = summary or {}
    project_title = summary.get("project_title") or "检索策略包"
    qa_status = summary.get("qa_status") or "未标注"
    print_button = (
        ""
        if home
        else (
            f'<button id="print-page" class="icon-button" type="button" title="打印本页" '
            f'aria-label="打印本页" data-i18n-title="print_page" '
            f'data-i18n-aria-label="print_page">{ICONS["print"]}</button>'
        )
    )
    language_button = (
        f'<button id="language-toggle" class="language-button" type="button" '
        f'title="切换为英文界面" aria-label="切换为英文界面">{ICONS["globe"]}'
        '<span class="language-code" aria-hidden="true">EN</span></button>'
    )
    title_key = {
        "index": "page_index_title",
        "scope_card": "page_scope_card_title",
        "query_pack": "page_query_pack_title",
        "candidate_list": "page_candidate_list_title",
        "usage_guide": "page_usage_guide_title",
    }.get(page_key, "page_index_title")
    main = (
        content
        if home
        else (
            '<main id="main-content" class="page-layout"><aside class="toc" aria-label="本页目录" '
            'data-i18n-aria-label="toc_aria"><div class="toc-inner"><p class="toc-title" '
            'data-i18n="toc_title">本页目录</p><nav id="toc-nav"></nav></div></aside>'
            f'<article class="document" data-page="{page_key}" data-qa-status="{html.escape(str(qa_status), quote=True)}">{content}</article></main>'
        )
    )
    footer = (
        ""
        if home
        else (
            '<footer class="site-footer"><span data-i18n="offline_package">QueryStrategist · 离线检索策略包</span>'
            '<span data-i18n="citation_warning">候选文献需人工核验后方可引用</span></footer>'
        )
    )
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        "style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:\">"
        f"<title>{html.escape(title)} | QueryStrategist</title><style>{CSS}</style></head>"
        f'<body data-title-key="{title_key}"><a class="skip-link" href="#main-content" '
        'data-i18n="skip_main">跳到主要内容</a>'
        '<header class="topbar"><a class="brand" href="index.html"><span class="brand-mark">QS</span>'
        '<span class="brand-name">QueryStrategist</span></a>'
        f'<span class="project-context" title="{html.escape(project_title, quote=True)}">{html.escape(project_title)}</span>'
        f'<nav class="primary-nav" aria-label="主要导航" data-i18n-aria-label="primary_nav">{_navigation(page_key, available_pages)}</nav>'
        f'<div class="header-tools">{language_button}{print_button}</div></header>'
        '<noscript><div class="noscript">交互增强未启用，全部文档内容仍可正常阅读。</div></noscript>'
        f"{main}{footer}<script>{JS}</script></body></html>\n"
    )


def index_page(available_pages, summary=None):
    summary = summary or {}
    project_title = summary.get("project_title") or "检索策略包"
    generated_on = summary.get("generated_on") or "未记录"
    query_count = summary.get("query_count", 0)
    candidate_count = summary.get("candidate_count", 0)
    verified_count = summary.get("verified_count", 0)
    oa_count = summary.get("oa_count", 0)
    writing_type = summary.get("writing_type") or "未记录"
    time_span = summary.get("time_span") or "未记录"
    qa_status = summary.get("qa_status") or "未标注"
    steps = []
    for number, key in enumerate(available_pages, start=1):
        _, title, description, icon_name = PAGE_META[key]
        _, title_key, description_key = PAGE_I18N[key]
        steps.append(
            f'<a class="step" href="{key}.html"><span class="step-icon">{ICONS[icon_name]}</span>'
            f'<span class="step-copy"><span class="step-number" data-i18n="step" data-number="{number}">步骤 {number}</span>'
            f'<span class="step-title" data-i18n="{title_key}">{html.escape(title)}</span></span>'
            f'<span class="step-desc" data-i18n="{description_key}">{html.escape(description)}</span></a>'
        )
    content = (
        '<main id="main-content" class="home-main"><section class="home-hero">'
        '<div><p class="home-kicker" data-i18n="home_kicker">QUERYSTRATEGIST / 离线检索工作台</p>'
        f"<h1>{html.escape(project_title)}</h1>"
        '<p class="home-lead" data-i18n="home_lead">从研究范围确认、检索式执行到候选文献筛选，所有内容均可离线浏览和复制。</p>'
        '<div class="meta-line">'
        f'<span><span data-i18n="generated_date">生成日期</span> <b>{html.escape(str(generated_on))}</b></span>'
        f'<span><span data-i18n="writing_type">写作类型</span> {_writing_type_markup(writing_type)}</span>'
        f'<span><span data-i18n="time_span">时间范围</span> <b>{html.escape(str(time_span))}</b></span></div></div>'
        '<aside class="overview-panel" aria-label="结果摘要" data-i18n-aria-label="result_summary"><h2 data-i18n="result_summary">结果摘要</h2>'
        f'<div class="overview-row"><span data-i18n="query_count">检索式</span><strong>{query_count} <span data-i18n="query_unit">条</span></strong></div>'
        f'<div class="overview-row"><span data-i18n="candidate_count">候选文献</span><strong>{candidate_count} <span data-i18n="record_unit">篇</span></strong></div>'
        f'<div class="overview-row"><span data-i18n="doi_verified">DOI 已验证</span><strong>{verified_count} <span data-i18n="record_unit">篇</span></strong></div>'
        f'<div class="overview-row"><span data-i18n="open_access">开放获取</span><strong>{oa_count} <span data-i18n="record_unit">篇</span></strong></div>'
        f'<div class="overview-row"><span data-i18n="qa_label">Query QA</span><strong>{_status_badge(qa_status)}</strong></div>'
        "</aside></section>"
        f'<nav class="pipeline" aria-label="策略包阅读流程" data-i18n-aria-label="pipeline_aria">{"".join(steps)}</nav>'
        '<p class="home-note" data-i18n="home_note">建议先确认研究范围，再使用推荐起步检索式。候选文献仅供筛选，正式引用前仍需核验题名、作者、年份、DOI 与全文内容。</p>'
        '<footer class="site-footer"><span data-i18n="offline_package">QueryStrategist · 离线检索策略包</span>'
        '<span data-i18n="local_files">本地自包含文件，无需联网</span></footer></main>'
    )
    return shell(
        "检索策略包", content, "index", available_pages, home=True, summary=summary
    )
