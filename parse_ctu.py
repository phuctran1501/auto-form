import urllib.request
import re

url = 'https://www.ctu.edu.vn/dao-tao/ctdt-dai-hoc.html'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8')
        # clean scripts
        html_clean = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
        html_clean = re.sub(r'<style.*?</style>', '', html_clean, flags=re.DOTALL)
        
        # find table rows
        rows = re.findall(r'<tr.*?</tr>', html_clean, re.DOTALL)
        print(f"Total rows found: {len(rows)}")
        majors = []
        for r in rows:
            tds = re.findall(r'<td.*?>(.*?)</td>', r, re.DOTALL)
            if tds:
                texts = [re.sub(r'<[^>]+>', '', td).strip() for td in tds]
                majors.append(texts)
        for m in majors[:25]:
            print("ROW:", m)
except Exception as e:
    print("Error:", e)

