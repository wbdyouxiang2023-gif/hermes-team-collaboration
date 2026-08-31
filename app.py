#!/usr/bin/env python3
"""WebPhone - Virtual phone in browser with built-in web proxy."""
import os, sys, re, json, time, threading
from urllib.parse import urljoin, urlparse, quote, unquote, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import ssl

PORT = 9000
PROXY_PREFIX = "wp?url="
UA_MOBILE = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

PHONE_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>WebPhone</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%;overflow:hidden}
body{background:#111;display:flex;justify-content:center;align-items:center;font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',Roboto,sans-serif}
.phone{width:390px;height:844px;background:#1a1a1a;border-radius:55px;padding:10px;box-shadow:0 0 0 2px #333,0 30px 80px rgba(0,0,0,.6);position:relative;user-select:none}
.screen{width:100%;height:100%;border-radius:46px;overflow:hidden;position:relative;background:#000}
.dynamic-island{position:absolute;top:12px;left:50%;transform:translateX(-50%);width:126px;height:36px;background:#000;border-radius:20px;z-index:200}
.status-bar{position:absolute;top:0;left:0;right:0;height:54px;display:flex;justify-content:space-between;align-items:center;padding:14px 28px 0;color:#fff;font-size:15px;font-weight:600;z-index:150;pointer-events:none}
.status-bar .right{display:flex;align-items:center;gap:6px;font-size:13px}
.battery{width:25px;height:12px;border:1.5px solid #fff;border-radius:3px;position:relative;display:inline-block;vertical-align:middle}
.battery::after{content:'';position:absolute;right:-4px;top:2px;width:2px;height:6px;background:#fff;border-radius:0 1px 1px 0}
.battery-fill{width:80%;height:100%;background:#34c759;border-radius:1.5px}
.lock-screen{position:absolute;inset:0;background:linear-gradient(160deg,#0f0c29,#302b63,#24243e);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:180;transition:transform .4s ease,opacity .4s ease;cursor:pointer}
.lock-screen.unlocked{transform:translateY(-100%);opacity:0;pointer-events:none}
.lock-time{font-size:82px;font-weight:200;color:#fff;letter-spacing:-2px}
.lock-date{font-size:20px;color:rgba(255,255,255,.8);margin-top:4px;font-weight:400}
.lock-hint{position:absolute;bottom:50px;color:rgba(255,255,255,.5);font-size:14px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:.4}50%{opacity:1}}
.home-screen{position:absolute;inset:0;background:linear-gradient(145deg,#667eea 0%,#764ba2 50%,#f093fb 100%);padding:60px 24px 100px;overflow-y:auto;scrollbar-width:none}
.home-screen::-webkit-scrollbar{display:none}
.search-bar{margin:0 0 20px;padding:10px 16px;background:rgba(255,255,255,.2);backdrop-filter:blur(15px);border-radius:14px;color:rgba(255,255,255,.7);font-size:15px;cursor:pointer;text-align:center;transition:background .2s}
.search-bar:hover{background:rgba(255,255,255,.3)}
.app-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:22px 0}
.app-icon{display:flex;flex-direction:column;align-items:center;gap:6px;cursor:pointer;transition:transform .15s}
.app-icon:active{transform:scale(.85)}
.app-icon .icon{width:62px;height:62px;border-radius:15px;display:flex;justify-content:center;align-items:center;font-size:30px;box-shadow:0 4px 15px rgba(0,0,0,.25);color:#fff}
.app-icon .label{color:#fff;font-size:11px;font-weight:500;text-shadow:0 1px 3px rgba(0,0,0,.3);max-width:70px;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dock{position:absolute;bottom:20px;left:24px;right:24px;height:88px;background:rgba(255,255,255,.18);backdrop-filter:blur(25px);-webkit-backdrop-filter:blur(25px);border-radius:28px;display:flex;justify-content:space-evenly;align-items:center;z-index:100}
.dock .app-icon .icon{width:58px;height:58px;border-radius:14px}
.home-bar{position:absolute;bottom:6px;left:50%;transform:translateX(-50%);width:140px;height:5px;background:rgba(255,255,255,.5);border-radius:3px;z-index:300;cursor:pointer}
.page-dots{display:flex;justify-content:center;gap:6px;margin-top:20px}
.page-dots .dot{width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.3)}
.page-dots .dot.active{background:#fff}
.app-view{position:absolute;inset:0;background:#fff;display:flex;flex-direction:column;z-index:160;transform:scale(.9);opacity:0;pointer-events:none;transition:transform .3s ease,opacity .3s ease;border-radius:0}
.app-view.active{transform:scale(1);opacity:1;pointer-events:all}
.app-view .app-header{height:54px;min-height:54px;display:flex;align-items:center;padding:0 16px;gap:12px;font-size:17px;font-weight:600;background:#f8f8f8;border-bottom:.5px solid #ddd}
.app-view .app-header .back-btn{font-size:24px;cursor:pointer;padding:4px 8px;border-radius:8px;color:#007aff}
.app-view .app-header .back-btn:hover{background:#e5e5ea}
.app-view .app-body{flex:1;overflow:auto;scrollbar-width:none}
.app-view .app-body::-webkit-scrollbar{display:none}
.browser-bar{display:flex;align-items:center;padding:8px 12px;gap:8px;background:#f2f2f7;border-bottom:.5px solid #c6c6c8}
.browser-bar .nav-btn{width:32px;height:32px;border:none;background:none;font-size:20px;cursor:pointer;border-radius:50%;color:#007aff;display:flex;align-items:center;justify-content:center}
.browser-bar .nav-btn:active{background:#ddd}
.browser-bar .url-input{flex:1;height:36px;border-radius:18px;border:none;background:#fff;padding:0 14px;font-size:15px;outline:none;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.browser-bar .go-btn{height:32px;padding:0 14px;border-radius:16px;border:none;background:#007aff;color:#fff;font-size:14px;font-weight:600;cursor:pointer}
.browser-bar .go-btn:active{background:#0056b3}
.browser-content{flex:1;overflow:auto;background:#fff;position:relative}
.browser-content iframe{width:100%;height:100%;border:none}
.browser-loading{display:none;position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;color:#8e8e93}
.browser-loading.show{display:block}
.browser-loading .spinner{width:40px;height:40px;border:3px solid #e5e5ea;border-top-color:#007aff;border-radius:50%;animation:spin .8s linear infinite;margin:0 auto 12px}
@keyframes spin{to{transform:rotate(360deg)}}
.browser-error{display:none;padding:40px 20px;text-align:center;color:#8e8e93}
.browser-error.show{display:block}
.browser-error .err-icon{font-size:48px;margin-bottom:12px}
.calc-display{background:#000;color:#fff;padding:20px 24px;text-align:right;font-size:64px;font-weight:300;min-height:120px;display:flex;align-items:flex-end;justify-content:flex-end;overflow:hidden}
.calc-expr{font-size:20px;color:#8e8e93;min-height:28px}
.calc-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:12px;background:#000}
.calc-btn{height:72px;border:none;border-radius:36px;font-size:28px;font-weight:400;cursor:pointer;transition:filter .1s}
.calc-btn:active{filter:brightness(1.3)}
.calc-btn.num{background:#333;color:#fff}
.calc-btn.op{background:#ff9f0a;color:#fff;font-size:32px}
.calc-btn.func{background:#a5a5a5;color:#000}
.calc-btn.zero{grid-column:span 2;border-radius:36px;text-align:left;padding-left:28px}
.notes-list{padding:12px}
.note-item{padding:14px 16px;border-bottom:.5px solid #e5e5ea;cursor:pointer}
.note-item:active{background:#f2f2f7}
.note-item .note-title{font-size:16px;font-weight:600;margin-bottom:4px}
.note-item .note-preview{font-size:14px;color:#8e8e93;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.note-item .note-time{font-size:12px;color:#c7c7cc;margin-top:4px}
.notes-empty{text-align:center;padding:60px 20px;color:#c7c7cc}
.notes-empty .icon{font-size:64px;margin-bottom:12px}
.note-editor{display:flex;flex-direction:column;height:100%}
.note-editor textarea{flex:1;border:none;outline:none;padding:16px;font-size:16px;line-height:1.6;resize:none;font-family:inherit}
.note-editor .note-title-input{border:none;outline:none;padding:16px 16px 8px;font-size:22px;font-weight:700}
.settings-list{padding:12px 16px}
.settings-group{background:#fff;border-radius:12px;overflow:hidden;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.settings-group-title{font-size:13px;color:#8e8e93;text-transform:uppercase;padding:0 16px 6px;font-weight:600}
.settings-item{display:flex;align-items:center;padding:14px 16px;border-bottom:.5px solid #f2f2f7;cursor:pointer}
.settings-item:last-child{border-bottom:none}
.settings-item:active{background:#f2f2f7}
.settings-item .si-icon{width:30px;height:30px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:17px;margin-right:14px;color:#fff}
.settings-item .si-label{flex:1;font-size:16px}
.settings-item .si-value{color:#8e8e93;font-size:16px}
.settings-item .si-arrow{color:#c7c7cc;font-size:14px}
@media(max-width:420px){.phone{width:100vw;height:100vh;border-radius:0;padding:0;box-shadow:none}.screen{border-radius:0}}
</style>
</head>
<body>
<div class="phone">
  <div class="screen" id="screen">
    <div class="dynamic-island"></div>
    <div class="status-bar">
      <span id="statusTime">9:41</span>
      <div class="right"><span style="font-size:14px">5G</span><span>📶</span><div class="battery"><div class="battery-fill"></div></div></div>
    </div>
    <div class="lock-screen" id="lockScreen" onclick="unlock()">
      <div class="lock-time" id="lockTime">09:41</div>
      <div class="lock-date" id="lockDate">8月31日 星期一</div>
      <div class="lock-hint">上滑解锁</div>
    </div>
    <div class="home-screen" id="homeScreen">
      <div class="search-bar" onclick="openApp('browser')">搜索</div>
      <div class="app-grid" id="appGrid"></div>
      <div class="page-dots"><div class="dot active"></div><div class="dot"></div></div>
    </div>
    <div class="dock" id="dock"></div>
    <div class="app-view" id="view-browser">
      <div class="app-header" style="padding:0">
        <div class="browser-bar">
          <button class="nav-btn" onclick="browserBack()">&larr;</button>
          <button class="nav-btn" onclick="browserForward()">&rarr;</button>
          <input class="url-input" id="urlInput" placeholder="输入网址或搜索" onkeydown="if(event.key==='Enter')navigate()">
          <button class="go-btn" onclick="navigate()">Go</button>
        </div>
      </div>
      <div class="browser-content" id="browserContent">
        <div class="browser-loading" id="browserLoading"><div class="spinner"></div><div>加载中...</div></div>
        <div class="browser-error" id="browserError"><div class="err-icon">!</div><div>无法加载页面</div></div>
      </div>
    </div>
    <div class="app-view" id="view-calculator">
      <div class="calc-display"><div style="width:100%"><div class="calc-expr" id="calcExpr"></div><div id="calcResult">0</div></div></div>
      <div class="calc-grid" id="calcGrid"></div>
    </div>
    <div class="app-view" id="view-notes">
      <div class="app-header"><span class="back-btn" onclick="closeApp('notes')">&larr;</span><span>备忘录</span></div>
      <div class="app-body" id="notesBody"></div>
    </div>
    <div class="app-view" id="view-settings">
      <div class="app-header"><span class="back-btn" onclick="closeApp('settings')">&larr;</span><span>设置</span></div>
      <div class="app-body"><div class="settings-list" id="settingsList"></div></div>
    </div>
    <div class="app-view" id="view-about">
      <div class="app-header"><span class="back-btn" onclick="closeApp('about')">&larr;</span><span>关于本机</span></div>
      <div class="app-body" style="padding:30px;text-align:center">
        <div style="font-size:80px;margin-bottom:16px">W</div>
        <div style="font-size:24px;font-weight:700">WebPhone</div>
        <div style="color:#8e8e93;margin-top:8px">v1.0</div>
        <div style="color:#8e8e93;margin-top:4px">阿里云 PAI-DSW</div>
        <div style="color:#8e8e93;margin-top:4px">CPU 64 | 28GB RAM</div>
      </div>
    </div>
    <div class="home-bar" onclick="goHome()"></div>
  </div>
</div>
<script>
const APPS=[
  {id:'browser',name:'浏览器',icon:'\u{1F310}',bg:'linear-gradient(135deg,#007aff,#5856d6)',dock:true},
  {id:'calculator',name:'计算器',icon:'\u{1F522}',bg:'linear-gradient(135deg,#ff9f0a,#ff3b30)',dock:true},
  {id:'notes',name:'备忘录',icon:'\u{1F4DD}',bg:'linear-gradient(135deg,#ffcc00,#ff9500)'},
  {id:'settings',name:'设置',icon:'\u2699',bg:'linear-gradient(135deg,#8e8e93,#636366)'},
  {id:'about',name:'关于本机',icon:'\u2139',bg:'linear-gradient(135deg,#64d2ff,#007aff)'},
  {id:'_baidu',name:'百度',icon:'B',bg:'linear-gradient(135deg,#2932e1,#1a49c4)',url:'https://www.baidu.com'},
  {id:'_bing',name:'Bing',icon:'b',bg:'linear-gradient(135deg,#00809d,#00607d)',url:'https://www.bing.com'},
  {id:'_github',name:'GitHub',icon:'G',bg:'linear-gradient(135deg,#333,#24292e)',url:'https://github.com'},
  {id:'_bilibili',name:'B\u7AD9',icon:'B',bg:'linear-gradient(135deg,#fb7299,#e04f7a)',url:'https://m.bilibili.com'},
  {id:'_zhihu',name:'知乎',icon:'\u77E5',bg:'linear-gradient(135deg,#0066ff,#0044cc)',url:'https://www.zhihu.com'},
  {id:'_weibo',name:'微博',icon:'\u5FAE',bg:'linear-gradient(135deg,#ff6b6b,#ee5a24)',url:'https://m.weibo.cn'},
  {id:'_taobao',name:'淘宝',icon:'\u6DD8',bg:'linear-gradient(135deg,#ff5000,#ff2d00)',url:'https://m.taobao.com'},
];
const DOCK_APPS=APPS.filter(a=>a.dock).concat([
  {id:'_phone',name:'电话',icon:'\u{1F4DE}',bg:'linear-gradient(135deg,#34c759,#248a3d)',action:'alert'}
]);
const HOME_APPS=APPS.filter(a=>!a.dock);
let currentApp=null,browserHistory=[],browserIdx=-1;
let calcExpr='',calcDisplay='0',calcNewNum=true,calcPendingOp=null,calcAccum=0;
let notes=JSON.parse(localStorage.getItem('wp_notes')||'[]');
let editingNote=null;
function init(){updateTime();setInterval(updateTime,1000);renderApps();renderDock();initCalc();renderNotes();renderSettings();}
function updateTime(){const n=new Date();const h=String(n.getHours()).padStart(2,'0');const m=String(n.getMinutes()).padStart(2,'0');const t=h+':'+m;document.getElementById('statusTime').textContent=t;document.getElementById('lockTime').textContent=t;const ds=['\u661F\u671F\u65E5','\u661F\u671F\u4E00','\u661F\u671F\u4E8C','\u661F\u671F\u4E09','\u661F\u671F\u56DB','\u661F\u671F\u4E94','\u661F\u671F\u516D'];document.getElementById('lockDate').textContent=(n.getMonth()+1)+'\u6708'+n.getDate()+'\u65E5 '+ds[n.getDay()];}
function unlock(){document.getElementById('lockScreen').classList.add('unlocked');}
function renderApps(){document.getElementById('appGrid').innerHTML=HOME_APPS.map(a=>'<div class="app-icon" onclick="openApp(\''+a.id+'\')"><div class="icon" style="background:'+a.bg+'">'+a.icon+'</div><div class="label">'+a.name+'</div></div>').join('');}
function renderDock(){document.getElementById('dock').innerHTML=DOCK_APPS.map(a=>'<div class="app-icon" onclick="openApp(\''+a.id+'\')"><div class="icon" style="background:'+a.bg+'">'+a.icon+'</div></div>').join('');}
function openApp(id){const app=APPS.find(a=>a.id===id)||DOCK_APPS.find(a=>a.id===id);if(!app)return;if(app.url){openBrowser(app.url);return;}if(app.action==='alert'){alert('电话功能开发中');return;}const v=document.getElementById('view-'+id);if(v){v.classList.add('active');currentApp=id;}}
function closeApp(id){const v=document.getElementById('view-'+id);if(v)v.classList.remove('active');currentApp=null;}
function goHome(){if(currentApp){closeApp(currentApp);return;}const ls=document.getElementById('lockScreen');if(!ls.classList.contains('unlocked')){unlock();return;}}
function openBrowser(url){document.getElementById('view-browser').classList.add('active');currentApp='browser';if(url){document.getElementById('urlInput').value=url;navigate();}}
function navigate(){let url=document.getElementById('urlInput').value.trim();if(!url)return;if(!url.match(/^https?:\/\//i)){if(url.includes('.')&&!url.includes(' '))url='https://'+url;else url='https://www.bing.com/search?q='+encodeURIComponent(url);}document.getElementById('urlInput').value=url;loadPage(url);}
function loadPage(url){const content=document.getElementById('browserContent');const loading=document.getElementById('browserLoading');const err=document.getElementById('browserError');loading.classList.add('show');err.classList.remove('show');content.querySelectorAll('iframe').forEach(f=>f.remove());content.querySelectorAll('div:not(.browser-loading):not(.browser-error)').forEach(d=>{if(d.parentElement===content)d.remove();});const iframe=document.createElement('iframe');iframe.style.display='none';iframe.sandbox='allow-same-origin allow-scripts allow-popups allow-forms';content.appendChild(iframe);window._BP=(function(){let p=location.pathname;if(!p.endsWith('/'))p=p.substring(0,p.lastIndexOf('/')+1);return p;})();const proxyUrl=window._BP+'wp?url='+encodeURIComponent(url);iframe.onload=function(){loading.classList.remove('show');iframe.style.display='block';};iframe.onerror=function(){loading.classList.remove('show');err.classList.add('show');};setTimeout(()=>{if(loading.classList.contains('show')){loading.classList.remove('show');fetchProxy(url);}},8000);try{iframe.src=proxyUrl;}catch(e){fetchProxy(url);}browserHistory=browserHistory.slice(0,browserIdx+1);browserHistory.push(url);browserIdx=browserHistory.length-1;}
function fetchProxy(url){const content=document.getElementById('browserContent');const err=document.getElementById('browserError');content.querySelectorAll('iframe').forEach(f=>f.remove());content.querySelectorAll('div:not(.browser-loading):not(.browser-error)').forEach(d=>{if(d.parentElement===content)d.remove();});fetch(window._BP+'wp?url='+encodeURIComponent(url)).then(r=>{if(!r.ok)throw new Error(r.status);return r.text();}).then(html=>{const div=document.createElement('div');div.style.cssText='width:100%;height:100%;overflow:auto;-webkit-overflow-scrolling:touch';div.innerHTML=html;content.appendChild(div);}).catch(()=>{err.classList.add('show');});}
function browserBack(){if(browserIdx>0){browserIdx--;loadPage(browserHistory[browserIdx]);}else goHome();}
function browserForward(){if(browserIdx<browserHistory.length-1){browserIdx++;loadPage(browserHistory[browserIdx]);}}
function initCalc(){const bs=[{t:'AC',c:'func',a:'calcClear()'},{t:'+/-',c:'func',a:'calcToggle()'},{t:'%',c:'func',a:'calcPercent()'},{t:'/',c:'op',a:"calcOp('/')"},{t:'7',c:'num',a:"calcNum('7')"},{t:'8',c:'num',a:"calcNum('8')"},{t:'9',c:'num',a:"calcNum('9')"},{t:'*',c:'op',a:"calcOp('*')"},{t:'4',c:'num',a:"calcNum('4')"},{t:'5',c:'num',a:"calcNum('5')"},{t:'6',c:'num',a:"calcNum('6')"},{t:'-',c:'op',a:"calcOp('-')"},{t:'1',c:'num',a:"calcNum('1')"},{t:'2',c:'num',a:"calcNum('2')"},{t:'3',c:'num',a:"calcNum('3')"},{t:'+',c:'op',a:"calcOp('+')"},{t:'0',c:'num zero',a:"calcNum('0')"},{t:'.',c:'num',a:'calcDot()'},{t:'=',c:'op',a:'calcEquals()'}];document.getElementById('calcGrid').innerHTML=bs.map(b=>'<button class="calc-btn '+b.c+'" onclick="'+b.a+'">'+b.t+'</button>').join('');}
function calcNum(n){if(calcNewNum){calcDisplay=n;calcNewNum=false;}else{calcDisplay=calcDisplay==='0'?n:calcDisplay+n;}calcExpr='';updateCalc();}
function calcDot(){if(calcNewNum){calcDisplay='0.';calcNewNum=false;}else if(!calcDisplay.includes('.')){calcDisplay+='.';}updateCalc();}
function calcOp(op){const v=parseFloat(calcDisplay);if(calcPendingOp&&!calcNewNum)calcAccum=calcEval(calcAccum,v,calcPendingOp);else calcAccum=v;calcPendingOp=op;calcExpr=calcAccum+' '+({'/':'/',
'*':'*','-':'-','+':'+'}[op]);calcNewNum=true;updateCalc();}
function calcEquals(){if(!calcPendingOp)return;const v=parseFloat(calcDisplay);const r=calcEval(calcAccum,v,calcPendingOp);calcExpr=calcAccum+' '+({'/':'/','*':'*','-':'-','+':'+'}[calcPendingOp])+' '+v+' =';calcDisplay=String(parseFloat(r.toFixed(10)));calcPendingOp=null;calcNewNum=true;updateCalc();}
function calcEval(a,b,op){switch(op){case'+':return a+b;case'-':return a-b;case'*':return a*b;case'/':return b!==0?a/b:'Error';}return b;}
function calcClear(){calcDisplay='0';calcExpr='';calcPendingOp=null;calcNewNum=true;calcAccum=0;updateCalc();}
function calcToggle(){calcDisplay=String(-parseFloat(calcDisplay));updateCalc();}
function calcPercent(){calcDisplay=String(parseFloat(calcDisplay)/100);updateCalc();}
function updateCalc(){document.getElementById('calcExpr').textContent=calcExpr;document.getElementById('calcResult').textContent=calcDisplay;}
function renderNotes(){const body=document.getElementById('notesBody');if(editingNote!==null){const note=notes[editingNote]||{title:'',body:'',time:Date.now()};body.innerHTML='<div class="note-editor"><input class="note-title-input" placeholder="标题" value="'+esc(note.title)+'" oninput="notes['+editingNote+'].title=this.value;saveNotes()"><textarea placeholder="开始输入..." oninput="notes['+editingNote+'].body=this.value;saveNotes()">'+esc(note.body)+'</textarea></div>';return;}if(!notes.length){body.innerHTML='<div class="notes-empty"><div class="icon">_</div><div>暂无备忘录</div><div style="margin-top:16px"><button onclick="newNote()" style="padding:10px 24px;border-radius:20px;border:none;background:#007aff;color:#fff;font-size:16px;cursor:pointer">新建</button></div></div>';return;}body.innerHTML='<div class="notes-list">'+notes.map((n,i)=>'<div class="note-item" onclick="editNote('+i+')"><div class="note-title">'+esc(n.title||'无标题')+'</div><div class="note-preview">'+esc(n.body||'')+'</div><div class="note-time">'+new Date(n.time).toLocaleString('zh-CN')+'</div></div>').join('')+'</div>';}
function editNote(i){editingNote=i;renderNotes();}
function newNote(){notes.unshift({title:'',body:'',time:Date.now()});editingNote=0;saveNotes();renderNotes();}
function saveNotes(){localStorage.setItem('wp_notes',JSON.stringify(notes));}
function esc(s){return(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function renderSettings(){document.getElementById('settingsList').innerHTML='<div class="settings-group-title">通用</div><div class="settings-group"><div class="settings-item" onclick="openApp(\'about\')"><div class="si-icon" style="background:#007aff">W</div><div class="si-label">关于本机</div><div class="si-arrow">&rsaquo;</div></div><div class="settings-item"><div class="si-icon" style="background:#34c759">S</div><div class="si-label">存储空间</div><div class="si-value">'+((localStorage.wp_notes||'').length/1024).toFixed(1)+' KB</div></div></div><div class="settings-group-title">网络</div><div class="settings-group"><div class="settings-item"><div class="si-icon" style="background:#007aff">P</div><div class="si-label">代理模式</div><div class="si-value">已启用</div></div></div>';}
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&currentApp)goHome();});
init();
</script>
</body>
</html>'''

SKIP_REWRITE = re.compile(r'^(javascript|data|blob|mailto|tel|#|about):', re.I)

def should_rewrite(url):
    url = url.strip()
    if not url or SKIP_REWRITE.match(url):
        return False
    return True

def rewrite_urls(html, base_url):
    def _rw(m):
        attr, q, url = m.group(1), m.group(2), m.group(3)
        if should_rewrite(url):
            return f'{attr}{q}{PROXY_PREFIX}{quote(urljoin(base_url, url))}{q}'
        return m.group(0)
    html = re.sub(r'((?:href|src|action|poster|data-src)\s*=\s*)(["\'])([^"\'\2]*?)\2', _rw, html, flags=re.I)
    def _rw_css(m):
        url = m.group(1)
        if should_rewrite(url):
            return f'url({PROXY_PREFIX}{quote(urljoin(base_url, url))})'
        return m.group(0)
    html = re.sub(r'url\(([^)]+)\)', _rw_css, html)
    html = re.sub(r'<meta[^>]*http-equiv\s*=\s*["\']?X-Frame-Options["\']?[^>]*/?>', '', html, flags=re.I)
    html = re.sub(r'<meta[^>]*http-equiv\s*=\s*["\']?Content-Security-Policy["\']?[^>]*/?>', '', html, flags=re.I)
    return html

def proxy_fetch(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        'User-Agent': UA_MOBILE,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    })
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        ct = resp.headers.get('Content-Type', 'application/octet-stream')
        data = resp.read()
        return data, ct, 200
    except urllib.error.HTTPError as e:
        ct = e.headers.get('Content-Type', 'text/plain')
        try: data = e.read()
        except: data = b''
        return data, ct, e.code
    except Exception as e:
        return str(e).encode(), 'text/plain', 502

class PhoneHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == '/' or parsed.path.endswith('/'):
            data = PHONE_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif parsed.path.endswith('/wp') or parsed.path == '/wp':
            url = qs.get('url', [''])[0]
            if not url:
                self._resp(400, b'Missing url', 'text/plain'); return
            url = unquote(url)
            data, ct, code = proxy_fetch(url)
            if 'text/html' in ct and code == 200:
                try:
                    text = data.decode('utf-8', errors='replace')
                    text = rewrite_urls(text, url)
                    data = text.encode('utf-8', errors='replace')
                except: pass
            self._resp(code, data, ct)
        else:
            self._resp(404, b'Not Found', 'text/plain')
    def do_POST(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path.endswith('/wp') or parsed.path == '/wp':
            url = qs.get('url', [''])[0]
            if not url:
                self._resp(400, b'Missing url', 'text/plain'); return
            url = unquote(url)
            data, ct, code = proxy_fetch(url)
            if 'text/html' in ct and code == 200:
                try:
                    text = data.decode('utf-8', errors='replace')
                    text = rewrite_urls(text, url)
                    data = text.encode('utf-8', errors='replace')
                except: pass
            self._resp(code, data, ct)
        else:
            self._resp(404, b'Not Found', 'text/plain')
    def _resp(self, code, data, ct):
        self.send_response(code)
        self.send_header('Content-Type', ct)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

class ReuseHTTPServer(HTTPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    server = ReuseHTTPServer(('0.0.0.0', PORT), PhoneHandler)
    print(f'WebPhone running on port {PORT}', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()
