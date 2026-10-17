import os
import threading
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, request, Response

import tool  # your original script: scraping + checking logic is reused as is

app = Flask(__name__)
lock = threading.Lock()


def fresh():
    return {"running": False, "phase": "idle", "done": 0, "total": 0, "scraped": 0,
            "counts": {"working": 0, "slow": 0, "blocked": 0, "dead": 0}, "working": []}


S = fresh()


def scrape():
    found = set()
    S.update(phase="scraping", done=0, total=len(tool.PROXY_SOURCES))

    def w(url):
        res = tool.scrape_from_url(url)
        with lock:
            found.update(res)
            S["done"] += 1

    with ThreadPoolExecutor(20) as ex:
        list(ex.map(w, tool.PROXY_SOURCES))
    S["scraped"] = len(found)
    return list(found)


def check(proxies, threads):
    chk = tool.ProxyChecker(check_discord=True)
    S.update(phase="checking", done=0, total=len(proxies))

    def one(p):
        try:
            st = chk.test_proxy(p)[0]
        except Exception:
            st = "dead"
        with lock:
            S["counts"][st] += 1
            S["done"] += 1
            if st == "working":
                S["working"].append(p)

    with ThreadPoolExecutor(threads) as ex:
        list(ex.map(one, proxies))


def job(mode, proxies, threads):
    try:
        if mode in ("scrape", "both"):
            proxies = scrape()
        if mode in ("check", "both") and proxies:
            check(proxies, threads)
        S["phase"] = "done"
    except Exception as e:
        S["phase"] = "error: " + str(e)[:80]
    finally:
        S["running"] = False


@app.route("/")
def index():
    return Response(PAGE, mimetype="text/html")


@app.route("/start", methods=["POST"])
def start():
    data = request.get_json(silent=True) or {}
    with lock:
        if S["running"]:
            return jsonify(error="busy"), 409
        mode = data.get("mode", "both")
        proxies = list(dict.fromkeys(tool.IP_PORT_REGEX.findall(data.get("proxies", ""))))
        threads = max(10, min(int(data.get("threads") or 50), 100))
        S.clear()
        S.update(fresh())
        S["running"] = True
    threading.Thread(target=job, args=(mode, proxies, threads), daemon=True).start()
    return jsonify(ok=True)


@app.route("/status")
def status():
    with lock:
        return jsonify(S)


@app.route("/download")
def download():
    with lock:
        body = "\n".join(S["working"])
    return Response(body, mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=working_proxies.txt"})


PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Austin Proxy</title>
<style>
:root{--bg:#0b0b12;--card:#161622;--p:#7903ff;--c:#03f8fc;--g:#44ff00;--y:#fcf803;--r:#ff5050;--d:#8c8e99}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:#fff;font-family:system-ui,Arial,sans-serif;padding:20px;min-height:100vh}
.w{max-width:760px;margin:0 auto}
h1{text-align:center;font-size:2.2rem;font-weight:900;color:var(--p);letter-spacing:1px}
.sub{text-align:center;color:var(--d);font-size:.85rem;margin:6px 0 22px}
.card{background:var(--card);border-radius:16px;padding:18px;margin-bottom:14px;border:1px solid #26263a}
.row{display:flex;gap:10px;flex-wrap:wrap}
button{flex:1;min-width:140px;padding:14px;border:0;border-radius:12px;color:#fff;font-weight:700;font-size:1rem;cursor:pointer}
.b1{background:var(--p)}.b2{background:#1a8cc0}.b3{background:#1fa63a}.b4{background:#2e2e44}
button:disabled{opacity:.5}
textarea,input{width:100%;background:#0f0f18;border:1px solid #2a2a40;border-radius:10px;color:#fff;padding:10px;font-family:monospace;font-size:.85rem}
textarea{height:110px;resize:vertical}
label{color:var(--d);font-size:.8rem;display:block;margin:10px 0 6px}
.bar{height:10px;background:#0f0f18;border-radius:6px;overflow:hidden;margin:10px 0}
.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--p),var(--c));transition:width .4s}
.st{color:var(--c);font-size:.9rem}
.cn{display:flex;justify-content:space-between;margin-top:8px;font-size:.95rem;flex-wrap:wrap;gap:6px}
</style></head><body><div class="w">
<h1>AUSTIN PROXY</h1>
<p class="sub">True Proxy Scraper &amp; Checker &nbsp;|&nbsp; Owned by Aqua Leaks</p>

<div class="card">
  <div class="row">
    <button class="b1" onclick="go('scrape')">Scrape Only</button>
    <button class="b3" onclick="go('both')">Scrape + Check</button>
  </div>
  <label>Or paste your own proxies to check (ip:port, one per line)</label>
  <textarea id="list" placeholder="1.2.3.4:8080"></textarea>
  <label>Threads (10 to 100)</label>
  <input id="th" type="number" value="50" min="10" max="100">
  <div class="row" style="margin-top:12px"><button class="b2" onclick="go('check')">Check My List</button></div>
</div>

<div class="card">
  <div class="st" id="st">Idle</div>
  <div class="bar"><i id="bar"></i></div>
  <div class="cn">
    <span style="color:var(--g)">Working <b id="w">0</b></span>
    <span style="color:var(--y)">Slow <b id="s">0</b></span>
    <span style="color:#ff9050">Blocked <b id="b">0</b></span>
    <span style="color:var(--r)">Dead <b id="d">0</b></span>
  </div>
</div>

<div class="card">
  <label style="margin-top:0">Working proxies</label>
  <textarea id="out" readonly style="height:180px"></textarea>
  <div class="row" style="margin-top:12px">
    <button class="b4" onclick="copyOut()">Copy</button>
    <button class="b4" onclick="location.href='/download'">Download .txt</button>
  </div>
</div>
</div>
<script>
const $=id=>document.getElementById(id);let t;
async function go(mode){
  const r=await fetch('/start',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({mode:mode,proxies:$('list').value,threads:+$('th').value||50})});
  if(r.status===409){alert('A job is already running. Please wait.');}
  poll();
}
function poll(){clearInterval(t);t=setInterval(async()=>{
  const s=await (await fetch('/status')).json();render(s);
  if(!s.running&&s.phase!=='idle')clearInterval(t);},1000);}
function render(s){
  const pct=s.total?Math.round(s.done/s.total*100):0;
  $('bar').style.width=pct+'%';
  let txt=s.phase==='scraping'?'Scraping sources... '+s.done+'/'+s.total:
          s.phase==='checking'?'Checking proxies... '+s.done+'/'+s.total:
          s.phase==='done'?'Done. Scraped '+s.scraped+' unique proxies.':s.phase;
  $('st').textContent=txt;
  $('w').textContent=s.counts.working;$('s').textContent=s.counts.slow;
  $('b').textContent=s.counts.blocked;$('d').textContent=s.counts.dead;
  $('out').value=s.working.join('\\n');
}
function copyOut(){const v=$('out').value;if(v){navigator.clipboard.writeText(v);}}
poll();
</script></body></html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
