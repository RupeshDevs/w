import os
import sys
import re
import time
import random
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from stealth_requests import StealthSession
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False


DISCORD_API = "https://discord.com/api/v9/experiments"
GENERAL_URL = "https://httpbin.org/ip"
TIMEOUT = 10
DEFAULT_THREADS = 50

INPUT_DIR = "input"
OUTPUT_DIR = "output"
PROXIES_FILE = os.path.join(INPUT_DIR, "proxies.txt")
SCRAPED_FILE = os.path.join(OUTPUT_DIR, "scraped.txt")
GOOD_FILE = os.path.join(OUTPUT_DIR, "good.txt")
DISCORD_GOOD_FILE = os.path.join(OUTPUT_DIR, "discord_good.txt")
SLOW_FILE = os.path.join(OUTPUT_DIR, "slow.txt")
BLOCKED_FILE = os.path.join(OUTPUT_DIR, "blocked.txt")
DEAD_FILE = os.path.join(OUTPUT_DIR, "dead.txt")

PROXY_SOURCES = [
    "https://cdn.jsdelivr.net/gh/proxyscrape/free-proxy-list@main/proxies/all/data.txt",
    "https://cdn.jsdelivr.net/gh/proxyscrape/free-proxy-list@main/proxies/protocols/http/data.txt",
    "https://cdn.jsdelivr.net/gh/proxyscrape/free-proxy-list@main/proxies/protocols/https/data.txt",
    "https://cdn.jsdelivr.net/gh/proxyscrape/free-proxy-list@main/proxies/protocols/socks4/data.txt",
    "https://cdn.jsdelivr.net/gh/proxyscrape/free-proxy-list@main/proxies/protocols/socks5/data.txt",
    "https://raw.githubusercontent.com/dinoz0rg/proxy-list/main/scraped_proxies/http.txt",
    "https://raw.githubusercontent.com/dinoz0rg/proxy-list/main/scraped_proxies/socks4.txt",
    "https://raw.githubusercontent.com/dinoz0rg/proxy-list/main/scraped_proxies/socks5.txt",
    "https://raw.githubusercontent.com/dinoz0rg/proxy-list/main/checked_proxies/http.txt",
    "https://raw.githubusercontent.com/dinoz0rg/proxy-list/main/checked_proxies/socks4.txt",
    "https://raw.githubusercontent.com/dinoz0rg/proxy-list/main/checked_proxies/socks5.txt",
    "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt",
    "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt",
    "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks4/data.txt",
    "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt",
    "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/proxy-free/free-proxy-list/main/all.txt",
    "https://raw.githubusercontent.com/proxy-free/free-proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/proxy-free/free-proxy-list/main/https.txt",
    "https://raw.githubusercontent.com/proxy-free/free-proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/proxy-free/free-proxy-list/main/socks5.txt",
    "https://cdn.jsdelivr.net/gh/officialputuid/KangProxy@main/xResults/Proxies.txt",
    "https://cdn.jsdelivr.net/gh/officialputuid/KangProxy@main/xResults/RAW.txt",
    "https://cdn.jsdelivr.net/gh/officialputuid/KangProxy@main/http/http.txt",
    "https://cdn.jsdelivr.net/gh/officialputuid/KangProxy@main/https/https.txt",
    "https://cdn.jsdelivr.net/gh/officialputuid/KangProxy@main/socks4/socks4.txt",
    "https://cdn.jsdelivr.net/gh/officialputuid/KangProxy@main/socks5/socks5.txt",
    "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/http.txt",
    "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/main/all.txt",
    "https://raw.githubusercontent.com/dpangestuw/Free-Proxy/refs/heads/main/All_proxies.txt",
    "https://raw.githubusercontent.com/dpangestuw/Free-Proxy/refs/heads/main/http_proxies.txt",
    "https://raw.githubusercontent.com/dpangestuw/Free-Proxy/refs/heads/main/socks4_proxies.txt",
    "https://raw.githubusercontent.com/dpangestuw/Free-Proxy/refs/heads/main/socks5_proxies.txt",
    "https://raw.githubusercontent.com/LoneKingCode/free-proxy-db/main/proxies/all.txt",
    "https://raw.githubusercontent.com/LoneKingCode/free-proxy-db/main/proxies/http.txt",
    "https://raw.githubusercontent.com/LoneKingCode/free-proxy-db/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/LoneKingCode/free-proxy-db/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks4.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
]

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76",
]

IP_PORT_REGEX = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}")


class C:
    P  = "\033[38;2;121;3;255m"
    C  = "\033[38;2;3;248;252m"
    G  = "\033[38;2;68;255;0m"
    Y  = "\033[38;2;252;248;3m"
    D  = "\033[38;2;92;94;91m"
    W  = "\033[97m"
    RD = "\033[38;2;255;80;80m"
    R  = "\033[0m"

BANNER_LINES = [
    " █████╗ ██╗   ██╗███████╗████████╗██╗███╗   ██╗    ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗",
    "██╔══██╗██║   ██║██╔════╝╚══██╔══╝██║████╗  ██║    ██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝",
    "███████║██║   ██║███████╗   ██║   ██║██╔██╗ ██║    ██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝ ",
    "██╔══██║██║   ██║╚════██║   ██║   ██║██║╚██╗██║    ██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝  ",
    "██║  ██║╚██████╔╝███████║   ██║   ██║██║ ╚████║    ██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║   ",
    "╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝╚═╝  ╚═══╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ",
    "",
    "True Proxy Scraper & Checker (50+ sources)",
    "Owned by Aqua Leaks",
]


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def ensure_dirs():
    for d in (INPUT_DIR, OUTPUT_DIR):
        os.makedirs(d, exist_ok=True)


def mask(proxy):
    if len(proxy) > 30:
        return proxy[:10] + "***" + proxy[-10:]
    return proxy


def clean_proxy_line(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    if "|" in line:
        line = line.split("|", 1)[0].strip()
    if " " in line:
        line = line.split(" ", 1)[0].strip()
    if "://" in line:
        line = line.split("://", 1)[1]
    if not line or ":" not in line:
        return ""
    return line


def load_file(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [clean_proxy_line(l) for l in f if l.strip()]
    return list(dict.fromkeys([l for l in lines if l]))


def save_file(path, items):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for i in items:
            f.write(i + "\n")


def wipe_file(path):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    open(path, "w").close()


def suppress_proxy_env():
    for k in ("NO_PROXY", "no_proxy", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"):
        os.environ.pop(k, None)


def print_banner():
    clear()
    try:
        term_w = os.get_terminal_size().columns
    except Exception:
        term_w = 90

    fixed_w = max(len(l) for l in BANNER_LINES if l)
    for line in BANNER_LINES:
        s = line.rstrip().ljust(fixed_w)
        pad = max(0, (term_w - fixed_w) // 2)
        print(C.P + " " * pad + s + C.R)
    print()

def scrape_from_url(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": random.choice(UAS)})
        if r.status_code != 200:
            return set()
        return set(IP_PORT_REGEX.findall(r.text))
    except Exception:
        return set()


def scrape_all():
    wipe_file(SCRAPED_FILE)
    print(f"{C.D}|{C.R} Scraping from {C.W}{len(PROXY_SOURCES)}{C.R} sources...\n")
    all_proxies = set()
    done = 0
    lock = threading.Lock()

    def worker(url):
        nonlocal done
        res = scrape_from_url(url)
        with lock:
            all_proxies.update(res)
            done += 1
            pct = int(done / len(PROXY_SOURCES) * 100)
            host = url.split("/")[2] if "/" in url else url
            print(f"  {C.P}{pct:3d}%{C.R} {C.C}{host[:40]:<40}{C.R} {C.D}+{len(res):>5}{C.R}")

    with ThreadPoolExecutor(max_workers=20) as exe:
        list(exe.map(worker, PROXY_SOURCES))

    return list(all_proxies)


def mode_scrape_only():
    print_banner()
    print(f"  {C.P}+------------------------------------------+{C.R}")
    print(f"  {C.P}|{C.R}  {C.C}Austin - Scrape Only{C.R}                   {C.P}|{C.R}")
    print(f"  {C.P}+------------------------------------------+{C.R}\n")

    scraped = scrape_all()
    print(f"\n  {C.G}OK{C.R} Total unique scraped: {C.W}{len(scraped)}{C.R}")

    save_file(SCRAPED_FILE, scraped)
    save_file(PROXIES_FILE, scraped)
    print(f"  {C.G}OK{C.R} Saved to {C.C}{SCRAPED_FILE}{C.R}")
    print(f"  {C.G}OK{C.R} Copied to {C.C}{PROXIES_FILE}{C.R}")


class ProxyChecker:
    def __init__(self, check_discord=True):
        self.check_discord = check_discord
        self.lock = threading.Lock()
        self.results = {"working": [], "slow": [], "blocked": [], "dead": []}
        self.progress = {"done": 0, "total": 0}

    def _session(self):
        if HAS_STEALTH:
            try:
                return StealthSession()
            except Exception:
                pass
        s = requests.Session()
        s.headers.update({
            "User-Agent": random.choice(UAS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        return s

    @staticmethod
    def build_proxy_dict(proxy, scheme="http"):
        if "://" in proxy:
            return {"http": proxy, "https": proxy}
        url = f"{scheme}://{proxy}"
        return {"http": url, "https": url}

    def test_proxy(self, proxy):
        masked = mask(proxy)

        try:
            s = self._session()
            start = time.time()
            r = s.get(GENERAL_URL, proxies=self.build_proxy_dict(proxy), timeout=TIMEOUT, verify=False)
            gen_time = round(time.time() - start, 2)
            if r.status_code != 200:
                return "dead", masked, 0, 0, "BAD_STATUS"
        except Exception as e:
            err = str(e)[:25]
            if "timeout" in err.lower() or "(28)" in err:
                return "dead", masked, 0, 0, "TIMEOUT"
            return "dead", masked, 0, 0, err or "ERR"

        if not self.check_discord:
            return "working", masked, gen_time, 0, "OK"

        try:
            s2 = self._session()
            start2 = time.time()
            r2 = s2.get(DISCORD_API, proxies=self.build_proxy_dict(proxy), timeout=TIMEOUT, verify=False)
            dc_time = round(time.time() - start2, 2)

            if r2.status_code == 200:
                if dc_time > 5:
                    return "slow", masked, gen_time, dc_time, "SLOW"
                return "working", masked, gen_time, dc_time, "OK"
            elif r2.status_code == 403:
                return "blocked", masked, gen_time, dc_time, "403_BLOCKED"
            else:
                return "blocked", masked, gen_time, dc_time, f"HTTP_{r2.status_code}"
        except Exception as e:
            err = str(e)[:25]
            if "timeout" in err.lower() or "(28)" in err:
                return "blocked", masked, gen_time, 0, "DC_TIMEOUT"
            return "blocked", masked, gen_time, 0, err or "ERR"

    def check_one(self, i, proxy, total):
        status, masked, gen_t, dc_t, reason = self.test_proxy(proxy)
        with self.lock:
            self.results[status].append(proxy)
            self.progress["done"] += 1
            done = self.progress["done"]

        pct = int(done / total * 100)

        if status == "working":
            tag = f"{C.G}[OK]{C.R}"
            detail = f"{C.G}DC OK{C.R} {C.D}({dc_t}s){C.R}"
        elif status == "slow":
            tag = f"{C.Y}[SLOW]{C.R}"
            detail = f"{C.Y}SLOW{C.R} {C.D}({dc_t}s){C.R}"
        elif status == "blocked":
            tag = f"{C.Y}[BLOCK]{C.R}"
            detail = f"{C.RD}BLOCKED{C.R} {C.D}({reason}){C.R}"
        else:
            tag = f"{C.RD}[DEAD]{C.R}"
            detail = f"{C.RD}DEAD{C.R} {C.D}({reason}){C.R}"

        with self.lock:
            print(f"  {pct:3d}% {tag} {C.D}#{i+1:04d}{C.R} {C.W}{masked}{C.R} -> {detail}")

    def run(self, proxies, threads):
        total = len(proxies)
        self.progress["total"] = total
        self.progress["done"] = 0
        for k in self.results:
            self.results[k].clear()

        print(f"\n  {C.D}|{C.R} Testing: {C.W}{total}{C.R} proxies")
        print(f"  {C.D}|{C.R} Threads: {C.W}{threads}{C.R}")
        state = "ENABLED" if self.check_discord else "DISABLED"
        color = C.G if self.check_discord else C.Y
        print(f"  {C.D}|{C.R} Discord: {color}{state}{C.R}\n")

        start = time.time()
        with ThreadPoolExecutor(max_workers=threads) as exe:
            futs = [exe.submit(self.check_one, i, p, total) for i, p in enumerate(proxies)]
            for f in as_completed(futs):
                try:
                    f.result()
                except Exception:
                    pass

        return round(time.time() - start, 1)


def dump_results(checker, overwrite_input=False):
    w = len(checker.results["working"])
    s = len(checker.results["slow"])
    b = len(checker.results["blocked"])
    d = len(checker.results["dead"])

    print(f"\n  {C.P}=========================================={C.R}")
    print(f"  {C.G}Working  : {w:4d}{C.R}")
    print(f"  {C.Y}Slow     : {s:4d}{C.R}  {C.D}(>5s response){C.R}")
    print(f"  {C.RD}Blocked  : {b:4d}{C.R}  {C.D}(proxy works, Discord rejects){C.R}")
    print(f"  {C.RD}Dead     : {d:4d}{C.R}")
    print(f"  {C.P}=========================================={C.R}\n")

    if w:
        save_file(DISCORD_GOOD_FILE, checker.results["working"])
        save_file(GOOD_FILE, checker.results["working"])
        print(f"  {C.G}OK{C.R} {w} working proxies -> {C.C}{DISCORD_GOOD_FILE}{C.R}")
        if overwrite_input:
            save_file(PROXIES_FILE, checker.results["working"])
            print(f"  {C.G}OK{C.R} Overwrote {C.C}{PROXIES_FILE}{C.R} with working proxies.")
    if s:
        save_file(SLOW_FILE, checker.results["slow"])
        print(f"  {C.Y}OK{C.R} {s} slow proxies -> {C.C}{SLOW_FILE}{C.R}")
    if b:
        save_file(BLOCKED_FILE, checker.results["blocked"])
        print(f"  {C.Y}OK{C.R} {b} blocked proxies -> {C.C}{BLOCKED_FILE}{C.R}")
    if d:
        save_file(DEAD_FILE, checker.results["dead"])
        print(f"  {C.RD}OK{C.R} {d} dead proxies -> {C.C}{DEAD_FILE}{C.R}")

    if w == 0 and s == 0:
        print(f"\n  {C.RD}WARN: no working proxies found.{C.R}")
        print(f"  {C.RD}Get fresh residential/mobile proxies before generating.{C.R}")


def mode_check_only():
    print_banner()
    print(f"  {C.P}+------------------------------------------+{C.R}")
    print(f"  {C.P}|{C.R}  {C.C}Austin - Check Only{C.R}                    {C.P}|{C.R}")
    print(f"  {C.P}+------------------------------------------+{C.R}\n")
    ensure_dirs()

    default_input = PROXIES_FILE if os.path.exists(PROXIES_FILE) else SCRAPED_FILE
    raw = input(f"  {C.Y}?{C.R} Input file {C.D}(default: {default_input}){C.R} >> ").strip()
    input_file = raw if raw else default_input

    if not os.path.exists(input_file):
        print(f"  {C.RD}ERR{C.R} File not found: {C.W}{input_file}{C.R}")
        return

    proxies = load_file(input_file)
    if not proxies:
        print(f"  {C.RD}ERR{C.R} No proxies in file.")
        return

    thr_raw = input(f"  {C.Y}?{C.R} Threads {C.D}(default: {DEFAULT_THREADS}){C.R} >> ").strip()
    threads = int(thr_raw) if thr_raw.isdigit() and int(thr_raw) > 0 else DEFAULT_THREADS

    disc_raw = input(f"  {C.Y}?{C.R} Validate against Discord? {C.D}[Y/n]{C.R} >> ").strip().lower()
    check_discord = disc_raw not in ("n", "no")

    checker = ProxyChecker(check_discord=check_discord)
    elapsed = checker.run(proxies, threads)
    print(f"\n  {C.D}Time: {elapsed}s{C.R}")
    dump_results(checker, overwrite_input=False)


def mode_scrape_and_check():
    print_banner()
    print(f"  {C.P}+------------------------------------------+{C.R}")
    print(f"  {C.P}|{C.R}  {C.C}Austin - Scrape + Check{C.R}                {C.P}|{C.R}")
    print(f"  {C.P}+------------------------------------------+{C.R}\n")
    ensure_dirs()

    print(f"  {C.C}[1/2]{C.R} Scraping...\n")
    scraped = scrape_all()
    print(f"\n  {C.G}OK{C.R} Scraped: {C.W}{len(scraped)}{C.R} unique proxies")

    if not scraped:
        print(f"  {C.RD}ERR{C.R} Nothing to check.")
        return

    save_file(SCRAPED_FILE, scraped)
    save_file(PROXIES_FILE, scraped)

    thr_raw = input(f"\n  {C.Y}?{C.R} Threads {C.D}(default: {DEFAULT_THREADS}){C.R} >> ").strip()
    threads = int(thr_raw) if thr_raw.isdigit() and int(thr_raw) > 0 else DEFAULT_THREADS

    print(f"\n  {C.C}[2/2]{C.R} Checking...\n")
    checker = ProxyChecker(check_discord=True)
    elapsed = checker.run(scraped, threads)
    print(f"\n  {C.D}Time: {elapsed}s{C.R}")
    dump_results(checker, overwrite_input=True)


def menu():
    print_banner()
    print(f"  {C.D}+------------------------------------------+{C.R}")
    print(f"  {C.D}|{C.R}  {C.C}Austin{C.R} {C.D}- Proxy Tool{C.R}                     {C.D}|{C.R}")
    print(f"  {C.D}|{C.R}  {C.D}Owned by Aqua Leaks{C.R}                     {C.D}|{C.R}")
    print(f"  {C.D}+------------------------------------------+{C.R}\n")
    print(f"  {C.P}[1]{C.R} {C.W}Scrape Only{C.R}       {C.D}- gather proxies from all sources{C.R}")
    print(f"  {C.P}[2]{C.R} {C.W}Check Only{C.R}        {C.D}- validate existing proxies{C.R}")
    print(f"  {C.P}[3]{C.R} {C.W}Scrape + Check{C.R}    {C.D}- full pipeline{C.R}")
    print(f"  {C.P}[4]{C.R} {C.W}Exit{C.R}\n")
    return input(f"  {C.Y}austin{C.R} {C.D}>{C.R} ").strip()


def main():
    suppress_proxy_env()
    ensure_dirs()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if os.name == "nt":
        os.system("")

    while True:
        choice = menu()
        if choice == "1":
            mode_scrape_only()
            input(f"\n  {C.Y}Press Enter to return...{C.R}")
        elif choice == "2":
            mode_check_only()
            input(f"\n  {C.Y}Press Enter to return...{C.R}")
        elif choice == "3":
            mode_scrape_and_check()
            input(f"\n  {C.Y}Press Enter to return...{C.R}")
        elif choice == "4":
            print(f"\n  {C.C}Goodbye, captain.{C.R}\n")
            break
        else:
            print(f"  {C.RD}Invalid option.{C.R}")
            time.sleep(0.8)


if __name__ == "__main__":
    main()
