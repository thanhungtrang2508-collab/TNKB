#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sinh web app theo dõi lịch chốt quyền: docs/index.html (1 file, dữ liệu nhúng sẵn).

Đọc data/lich_su_kien.csv (do build_events.py tạo) + scripts/app_template.html,
nhúng dữ liệu dạng JSON gọn vào template rồi ghi ra docs/index.html.

Cách dùng: python3 scripts/build_app.py
"""
import json
import os
from datetime import datetime

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "data", "lich_su_kien.csv")
TEMPLATE = os.path.join(ROOT, "scripts", "app_template.html")
OUT = os.path.join(ROOT, "docs", "index.html")
STAMP = os.path.join(ROOT, "data", "last_updated.txt")

# Thứ tự cột nhúng (khớp với F trong template):
# [mã, sàn, tênDN, nhóm, sựKiện, chiTiết, tỷLệ, tiềnMặt, GDKHQ, ĐKCC, thựcHiện, TMkỳTrước, ngàyKỳTrước, soSánh]
COLS = ["Mã CP", "Sàn", "Tên DN", "Nhóm", "Loại sự kiện", "Chi tiết", "Tỷ lệ",
        "Tiền mặt (đ/cp)", "Ngày GDKHQ", "Ngày ĐKCC (chốt quyền)", "Ngày thực hiện",
        "Cổ tức TM kỳ trước (đ/cp)", "Ngày kỳ trước", "So với kỳ trước"]


def main():
    df = pd.read_csv(CSV, dtype=str).fillna("")
    rows = df[COLS].values.tolist()
    data_js = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))

    updated = datetime.now().strftime("%d/%m/%Y %H:%M")
    if os.path.exists(STAMP):  # ưu tiên mốc thời gian lúc quét dữ liệu
        with open(STAMP, encoding="utf-8") as f:
            txt = f.read().strip()
        if ":" in txt:
            updated = txt.split(":", 1)[1].strip()

    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("__DATA__", data_js).replace("__UPDATED__", updated)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    size_kb = os.path.getsize(OUT) // 1024
    print(f"[✓] Đã tạo {OUT} ({len(rows)} sự kiện, {size_kb} KB)")


if __name__ == "__main__":
    main()
