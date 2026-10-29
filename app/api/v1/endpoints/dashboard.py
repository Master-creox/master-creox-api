"""Master CreoX API dashboard (v0.6.0).

A professional HTML dashboard, not a replacement for /docs.
The page itself is public HTML; every data call still needs the
admin key, which the browser keeps only in its own localStorage
(never hardcoded, never sent to Muse, never stored server-side).
Panels: live status, key auto-generation, key list, key detail,
and line-by-line usage.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Master CreoX API — Dashboard</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:'Segoe UI',system-ui,Arial,sans-serif;background:#050a12;color:#dbeafe}
header{padding:16px 28px;background:#08111e;border-bottom:1px solid #22d3ee;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
.brand{font-size:19px;font-weight:700;letter-spacing:2px}.brand span{color:#22d3ee}
.tag{color:#94a3b8;font-size:12px;letter-spacing:1px}
.strip{display:flex;gap:22px;flex-wrap:wrap;padding:12px 28px;background:#071426;border-bottom:1px solid rgba(34,211,238,.3);font-size:13px;letter-spacing:1px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:14px}@media(max-width:900px){.grid{grid-template-columns:1fr}}
.panel{background:#0a1526;border:1px solid #1e3a5f;border-radius:8px;padding:18px}
.panel h2{margin:0 0 12px;font-size:12px;letter-spacing:2px;color:#7dd3fc;text-transform:uppercase}
label{font-size:13px;color:#94a3b8}input[type=text],input[type=password]{width:100%;padding:9px;margin:6px 0 12px;background:#071426;border:1px solid #1e3a5f;border-radius:6px;color:#fff}
button{background:#22d3ee;border:0;padding:9px 16px;border-radius:6px;font-weight:700;cursor:pointer;color:#082f49;margin-right:8px;margin-bottom:8px}
button.secondary{background:#0a1526;color:#22d3ee;border:1px solid #22d3ee}
.small{color:#94a3b8;font-size:13px;line-height:1.6}.mono{font-family:Consolas,monospace;word-break:break-all;background:#071426;padding:10px;border-radius:6px;border:1px solid #1e3a5f}
table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid #1e3a5f;padding:8px;text-align:left;font-size:13px}th{color:#7dd3fc;font-size:11px;letter-spacing:1px;text-transform:uppercase}
a{color:#22d3ee}.warn{color:#fbbf24}.ok{color:#34d399}.bad{color:#f43f5e}
</style></head><body>
<header><div><div class="brand">MASTER <span>CREOX API</span></div><div class="tag">DASHBOARD — KEYS, DETAILS &amp; LINE-BY-LINE USAGE</div></div><div><button onclick="loadAll()">Refresh</button><a href="/docs" style="margin-left:8px">API Docs</a></div></header>
<div class="strip"><span>SERVICE: <b class="ok" id="st-service">—</b></span><span>VERSION: <b id="st-version">—</b></span><span>ACTIVE KEYS: <b id="st-keys">—</b></span><span>TOTAL REQUESTS: <b id="st-req">—</b></span><span>REQUESTS TODAY: <b id="st-today">—</b></span><span id="st-time">LAST UPDATED: —</span></div>
<div class="grid">
<div class="panel"><h2>Admin Access</h2>
<label>Admin key (X-Admin-Key) — browser localStorage only, never hardcoded</label>
<input type="password" id="adminkey" placeholder="Paste MASTER_CREOX_ADMIN_KEY here">
<button onclick="saveKey()">Save in this browser</button><button class="secondary" onclick="clearKey()">Clear</button>
<p class="small" id="authmsg">Without the admin key, key creation and key details will return 401. The key is sent only as a header to this API.</p></div>
<div class="panel"><h2>Generate Key — Auto</h2>
<label>Key name</label><input type="text" id="keyname" placeholder="e.g. aegis-prime">
<label>Scopes</label><div style="margin:6px 0 12px"><label><input type="checkbox" class="scope" value="chat" checked> chat</label> &nbsp; <label><input type="checkbox" class="scope" value="tools" checked> tools</label></div>
<button onclick="genKey()">Generate key</button>
<div id="newkey"></div>
<p class="small warn">New key is shown only once. Copy it now and store it safely — it will never be shown again.</p></div>
</div>
<div class="grid">
<div class="panel"><h2>All Keys</h2><div id="keylist" class="small">Load with admin key, then Refresh.</div></div>
<div class="panel"><h2>Key Detail</h2><div id="keydetail" class="small">Click Details on any key above.</div></div>
</div>
<div style="padding:0 14px 20px"><div class="panel"><h2>Usage — Line by Line</h2><div id="usagelog" class="small">Load with admin key, then Refresh.</div></div></div>
<script>
var API = "/api/v1";
function adminHeaders(){ var k = localStorage.getItem("creox_admin_key") || ""; return k ? {"X-Admin-Key": k} : {}; }
function saveKey(){ var v = document.getElementById("adminkey").value.trim(); if(v){ localStorage.setItem("creox_admin_key", v); document.getElementById("authmsg").textContent = "Admin key saved in this browser only."; } loadAll(); }
function clearKey(){ localStorage.removeItem("creox_admin_key"); document.getElementById("adminkey").value = ""; document.getElementById("authmsg").textContent = "Admin key cleared from this browser."; }
function esc(s){ return String(s == null ? "" : s).replace(/&/g,"&amp;").replace(/</g,"&lt;"); }
function loadAll(){ loadStatus(); loadKeys(); loadUsage(); }
function loadStatus(){
  fetch(API + "/health").then(function(r){ return r.json(); }).then(function(d){
    document.getElementById("st-service").textContent = d.status || "ok";
    document.getElementById("st-version").textContent = d.version || "";
  }).catch(function(){});
  fetch(API + "/admin/stats", {headers: adminHeaders()}).then(function(r){ return r.json(); }).then(function(d){
    if(d.active_keys == null) return;
    document.getElementById("st-keys").textContent = d.active_keys;
    document.getElementById("st-req").textContent = d.total_requests;
    document.getElementById("st-today").textContent = d.requests_today;
    document.getElementById("st-time").textContent = "LAST UPDATED: " + new Date().toLocaleString("en-IN", {timeZone: "Asia/Kolkata"});
  }).catch(function(){});
}
function loadKeys(){
  fetch(API + "/keys", {headers: adminHeaders()}).then(function(r){ return r.json(); }).then(function(d){
    if(!d.keys){ document.getElementById("keylist").innerHTML = "<span class='bad'>Admin key required (401) — paste it above and Save.</span>"; return; }
    var rows = d.keys.map(function(k){ return "<tr><td>" + k.id + "</td><td><b>" + esc(k.name) + "</b></td><td>" + esc(k.scopes.join(", ")) + "</td><td>" + k.usage_count + "</td><td>" + esc(k.last_used_at || "never") + "</td><td>" + (k.revoked ? "<span class='bad'>revoked</span>" : "<span class='ok'>active</span>") + "</td><td><button onclick='showDetail(" + k.id + ")'>Details</button> <button class='secondary' onclick='revokeKey(" + k.id + ")'>Revoke</button></td></tr>"; }).join("");
    document.getElementById("keylist").innerHTML = "<table><tr><th>ID</th><th>Name</th><th>Scopes</th><th>Uses</th><th>Last used</th><th>Status</th><th>Action</th></tr>" + rows + "</table>";
  }).catch(function(){});
}
function genKey(){
  var name = document.getElementById("keyname").value.trim();
  var scopes = Array.prototype.slice.call(document.querySelectorAll(".scope:checked")).map(function(c){ return c.value; });
  if(!name){ alert("Key name likho pehle."); return; }
  fetch(API + "/keys", {method: "POST", headers: Object.assign({"Content-Type": "application/json"}, adminHeaders()), body: JSON.stringify({name: name, scopes: scopes})}).then(function(r){ return r.json(); }).then(function(d){
    if(!d.key){ document.getElementById("newkey").innerHTML = "<p class='bad'>" + esc(d.message || d.error || "Failed — check admin key.") + "</p>"; return; }
    document.getElementById("newkey").innerHTML = "<p>New key <b>ID " + d.id + "</b> — " + esc(d.name) + " — scopes: " + esc(d.scopes.join(", ")) + "</p><div class='mono'>" + esc(d.key) + "</div><button onclick='navigator.clipboard.writeText(document.querySelector(\"#newkey .mono\").textContent)'>Copy key</button>";
    loadKeys();
  });
}
function showDetail(id){
  fetch(API + "/keys/" + id, {headers: adminHeaders()}).then(function(r){ return r.json(); }).then(function(d){
    if(!d.key){ document.getElementById("keydetail").innerHTML = "<span class='bad'>Not found / not yours.</span>"; return; }
    var k = d.key;
    var rows = (d.recent || []).map(function(r){ return "<tr><td>" + esc(r.created_at) + "</td><td>" + esc(r.method) + "</td><td>" + esc(r.endpoint) + "</td><td>" + r.status_code + "</td><td>" + r.latency_ms + " ms</td><td>" + esc(r.model || "") + "</td><td>" + (r.tokens == null ? "" : r.tokens) + "</td></tr>"; }).join("") || "<tr><td colspan='7'>No usage yet for this key.</td></tr>";
    document.getElementById("keydetail").innerHTML = "<p><b>ID " + k.id + " — " + esc(k.name) + "</b><br>Scopes: " + esc(k.scopes.join(", ")) + "<br>Created: " + esc(k.created_at) + "<br>Last used: " + esc(k.last_used_at || "never") + "<br>Total uses: " + k.usage_count + "<br>Requests in usage log: " + d.usage.total_requests + ", tokens: " + d.usage.total_tokens + "</p><table><tr><th>Time</th><th>Method</th><th>Endpoint</th><th>Status</th><th>Latency</th><th>Model</th><th>Tokens</th></tr>" + rows + "</table>";
  });
}
function revokeKey(id){ if(!confirm("Key ID " + id + " revoke kar dun?")) return; fetch(API + "/keys/" + id, {method: "DELETE", headers: adminHeaders()}).then(function(){ loadKeys(); }); }
function loadUsage(){
  fetch(API + "/admin/usage/recent?limit=50", {headers: adminHeaders()}).then(function(r){ return r.json(); }).then(function(d){
    if(!d.recent){ document.getElementById("usagelog").innerHTML = "<span class='bad'>Admin key required (401).</span>"; return; }
    var rows = d.recent.map(function(r){ return "<tr><td>" + esc(r.created_at) + "</td><td>" + (r.key_id == null ? "" : r.key_id) + "</td><td>" + esc(r.method) + "</td><td>" + esc(r.endpoint) + "</td><td>" + r.status_code + "</td><td>" + r.latency_ms + " ms</td><td>" + esc(r.model || "") + "</td><td>" + (r.tokens == null ? "" : r.tokens) + "</td></tr>"; }).join("") || "<tr><td colspan='8'>No usage yet.</td></tr>";
    document.getElementById("usagelog").innerHTML = "<table><tr><th>Time</th><th>Key ID</th><th>Method</th><th>Endpoint</th><th>Status</th><th>Latency</th><th>Model</th><th>Tokens</th></tr>" + rows + "</table>";
  }).catch(function(){});
}
(function(){ var k = localStorage.getItem("creox_admin_key"); if(k) document.getElementById("adminkey").value = k; loadAll(); setInterval(loadStatus, 15000); })();
</script></body></html>
"""


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    return HTML
