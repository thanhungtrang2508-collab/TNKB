#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tạo bản tin tóm tắt buổi sáng: các sự kiện chốt quyền/cổ tức CỦA HÔM NAY
(+ nhìn nhanh 7 ngày tới), xuất ra HTML để gửi email lúc 9h sáng.

Đầu ra:
  /tmp/summary_email.html  - nội dung email (HTML)
  /tmp/summary_subject.txt - tiêu đề email
Mỗi mã trong email là link nhảy thẳng vào app: <APP_URL>#<MÃ>

Cách dùng: python3 scripts/build_summary.py
"""
import csv
import os
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "data", "lich_su_kien.csv")
APP_URL = "https://thanhungtrang2508-collab.github.io/TNKB/"

C = {  # tên cột -> khóa ngắn
    "Mã CP": "t", "Sàn": "x", "Tên DN": "n", "Loại sự kiện": "e", "Chi tiết": "d",
    "Tỷ lệ": "ratio", "Tiền mặt (đ/cp)": "cash", "Ngày GDKHQ": "g",
    "Ngày ĐKCC (chốt quyền)": "r", "Ngày thực hiện": "exe", "So với kỳ trước": "c",
}


def load():
    rows = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            rows.append({k: (raw.get(col) or "").strip() for col, k in C.items()})
    return rows


def money(v):
    try:
        return f"{float(v):,.0f}".replace(",", ".") + "đ"
    except (TypeError, ValueError):
        return ""


def val(r):
    return " · ".join(x for x in [money(r["cash"]), r["ratio"]] if x)


def fmt(d):
    return f"{d[8:10]}/{d[5:7]}" if d else ""


def cmp_color(c):
    if c.startswith("Tăng"):
        return "#067647"
    if c.startswith("Giảm"):
        return "#b42318"
    return "#68748a"


def table(rows, tag):
    tr = []
    for r in rows:
        cmp_html = (f'<span style="color:{cmp_color(r["c"])};font-size:12px">{r["c"]}</span>'
                    if r["c"] else "")
        tr.append(f"""<tr>
<td style="padding:7px 9px;border-bottom:1px solid #e9edf3">
  <a href="{APP_URL}#{r['t']}" style="font-weight:700;color:#1a56db;text-decoration:none">{r['t']}</a>
  <span style="color:#98a2b3;font-size:11px">{r['x']}</span><br>
  <span style="color:#68748a;font-size:11px">{r['n']}</span></td>
<td style="padding:7px 9px;border-bottom:1px solid #e9edf3;font-size:13px">{r['e']}<br>{cmp_html}</td>
<td style="padding:7px 9px;border-bottom:1px solid #e9edf3;font-weight:700;white-space:nowrap">{val(r)}</td>
<td style="padding:7px 9px;border-bottom:1px solid #e9edf3;font-size:12px;white-space:nowrap">{tag(r)}</td>
</tr>""")
    return ('<table style="border-collapse:collapse;width:100%;background:#fff;'
            'border:1px solid #e9edf3;border-radius:8px">' + "".join(tr) + "</table>")


def main():
    rows = load()
    ts = date.today().isoformat()
    in7 = (date.today() + timedelta(days=7)).isoformat()

    ex_today = [r for r in rows if r["g"] == ts]
    pay_today = [r for r in rows if r["exe"] == ts and r["g"] != ts]
    upcoming = sorted((r for r in rows if ts < r["g"] <= in7), key=lambda r: r["g"])

    today_vn = datetime.now().strftime("%d/%m/%Y")
    parts = [f"""<div style="font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:640px;margin:auto;color:#1c2433">
<h2 style="margin:6px 0">📅 Bản tin chốt quyền sáng {today_vn}</h2>
<p style="color:#68748a;font-size:13px;margin:4px 0 14px">
Bấm vào mã để mở chi tiết trong app · <a href="{APP_URL}" style="color:#1a56db">Mở bảng theo dõi đầy đủ →</a></p>"""]

    if ex_today:
        parts.append(f'<h3 style="margin:14px 0 6px">🟡 Hôm nay GDKHQ ({len(ex_today)} sự kiện)</h3>'
                     '<p style="color:#92400e;font-size:12px;margin:0 0 6px">Mua từ hôm nay sẽ KHÔNG được hưởng quyền các đợt dưới đây.</p>'
                     + table(ex_today, lambda r: "ĐKCC " + fmt(r["r"])))
    if pay_today:
        parts.append(f'<h3 style="margin:14px 0 6px">💰 Hôm nay chi trả ({len(pay_today)} sự kiện)</h3>'
                     + table(pay_today, lambda r: "tiền/CP về hôm nay"))
    if not ex_today and not pay_today:
        parts.append('<p style="background:#f4f6fb;padding:12px;border-radius:8px">'
                     'Hôm nay không có sự kiện chốt quyền hay chi trả nào.</p>')
    if upcoming:
        parts.append(f'<h3 style="margin:14px 0 6px">🔜 7 ngày tới ({len(upcoming)} sự kiện GDKHQ)</h3>'
                     + table(upcoming[:25], lambda r: "GDKHQ " + fmt(r["g"])))
        if len(upcoming) > 25:
            parts.append(f'<p style="color:#68748a;font-size:12px">… và {len(upcoming)-25} sự kiện khác — xem trong app.</p>')

    parts.append('<p style="color:#98a2b3;font-size:11px;margin-top:16px">Nguồn: vnstock (VCI), '
                 'chỉ để tham khảo. Bản tin tự động từ repo TNKB.</p></div>')

    with open("/tmp/summary_email.html", "w", encoding="utf-8") as f:
        f.write("".join(parts))
    n = len(ex_today) + len(pay_today)
    subject = (f"📅 {today_vn}: {len(ex_today)} mã GDKHQ, {len(pay_today)} mã chi trả hôm nay"
               if n else f"📅 {today_vn}: không có sự kiện hôm nay, {len(upcoming)} sự kiện trong 7 ngày tới")
    with open("/tmp/summary_subject.txt", "w", encoding="utf-8") as f:
        f.write(subject)
    print(f"[✓] {subject}")
    print(f"[✓] Đã ghi /tmp/summary_email.html ({os.path.getsize('/tmp/summary_email.html')//1024} KB)")


if __name__ == "__main__":
    main()
