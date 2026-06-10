#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lập bảng LỊCH SỰ KIỆN QUYỀN (chốt quyền / chia cổ tức) cho cổ phiếu Việt Nam.

Nguồn dữ liệu: thư viện vnstock (nguồn VCI).
Đầu ra: data/lich_su_kien.csv (+ .xlsx nếu có openpyxl).

Mỗi dòng = 1 sự kiện quyền của 1 mã, gồm:
  - Mã CP, Sàn, Tên DN
  - Loại sự kiện (cổ tức tiền mặt / cổ phiếu, ĐHĐCĐ, phát hành...)
  - Tỷ lệ, Số tiền/cp
  - Ngày GDKHQ (giao dịch không hưởng quyền)
  - Ngày ĐKCC (đăng ký cuối cùng = ngày chốt quyền)
  - Ngày thực hiện / thanh toán

Cách dùng:
  python3 scripts/build_events.py                 # toàn thị trường
  python3 scripts/build_events.py --symbols HPG,VNM,FPT
  python3 scripts/build_events.py --exchange HOSE --limit 50
  python3 scripts/build_events.py --past-days 30 --future-days 120
"""
import argparse
import contextlib
import io
import sys
import time
import warnings
from datetime import datetime, timedelta

import pandas as pd

warnings.filterwarnings("ignore")


@contextlib.contextmanager
def _quiet():
    """Nuốt banner quảng cáo mà vnstock in ra stdout."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield


with _quiet():
    from vnstock import Vnstock

_V = Vnstock()

# Các nhóm sự kiện liên quan tới "quyền". DIVIDEND là trọng tâm (cổ tức).
CATEGORY_LABEL = {
    "DIVIDEND": "Cổ tức / Phát hành",
    "SHAREHOLDER_MEETING": "ĐHĐCĐ / Lấy ý kiến",
    "ISSUE": "Phát hành thêm",
}
DEFAULT_CATEGORIES = ["DIVIDEND", "SHAREHOLDER_MEETING"]

# Cột đầu ra (header tiếng Việt) -> tên cột nguồn
OUTPUT_COLUMNS = [
    ("Mã CP", "ticker"),
    ("Sàn", "exchange"),
    ("Tên DN", "organ_name"),
    ("Nhóm", "category_label"),
    ("Loại sự kiện", "event_name_vi"),
    ("Chi tiết", "event_title_vi"),
    ("Tỷ lệ", "ty_le"),
    ("Tiền mặt (đ/cp)", "value_per_share"),
    ("Ngày GDKHQ", "exright_date"),
    ("Ngày ĐKCC (chốt quyền)", "record_date"),
    ("Ngày thực hiện", "exercise_date"),
]


def get_universe(scope_exchange=None, symbols=None, limit=None):
    """Trả về DataFrame: symbol, exchange, organ_name (chỉ cổ phiếu)."""
    with _quiet():
        listing = _V.stock(symbol="ACB", source="VCI").listing
        df = listing.symbols_by_exchange()
    df = df[df["type"] == "stock"].copy()
    if symbols:
        wanted = {s.strip().upper() for s in symbols}
        df = df[df["symbol"].isin(wanted)]
    if scope_exchange:
        df = df[df["exchange"].str.upper() == scope_exchange.upper()]
    df = df.sort_values("symbol").reset_index(drop=True)
    if limit:
        df = df.head(limit)
    return df[["symbol", "exchange", "organ_name"]]


def fetch_events(symbol, retries=2, rate_waits=10):
    """Lấy sự kiện của 1 mã.

    Chịu được giới hạn API: khi vnstock chạm rate-limit nó gọi sys.exit
    (SystemExit) -> ta bắt lại, nghỉ ~62s cho cửa sổ 1 phút reset rồi thử tiếp.
    Trả về DataFrame rỗng nếu lỗi khác/không có dữ liệu.
    """
    attempt = 0
    waits = 0
    while True:
        try:
            with _quiet():
                df = _V.stock(symbol=symbol, source="VCI").company.events()
            return df if df is not None else pd.DataFrame()
        except SystemExit:
            if waits >= rate_waits:
                return pd.DataFrame()
            waits += 1
            print(f"    [rate-limit] nghỉ 62s rồi thử lại {symbol} ...", file=sys.stderr)
            time.sleep(62)
        except Exception:
            attempt += 1
            if attempt > retries:
                return pd.DataFrame()
            time.sleep(1.5 * attempt)


def _fmt_ratio(row):
    """Hiển thị tỷ lệ thân thiện: 0.10 -> '10%'."""
    r = row.get("exercise_ratio")
    if pd.isna(r):
        return ""
    try:
        return f"{float(r) * 100:g}%"
    except (TypeError, ValueError):
        return str(r)


def _date_only(val):
    if pd.isna(val) or val in ("", None):
        return ""
    s = str(val)
    return s[:10]  # '2026-05-26T00:00:00' -> '2026-05-26'


def build(args):
    uni = get_universe(args.exchange,
                       args.symbols.split(",") if args.symbols else None,
                       args.limit)
    meta = {r.symbol: (r.exchange, r.organ_name) for r in uni.itertuples()}
    total = len(uni)
    print(f"[i] Quét {total} mã ...", file=sys.stderr)

    cats = set(args.categories.split(",")) if args.categories else set(DEFAULT_CATEGORIES)
    today = datetime.now().date()
    lo = today - timedelta(days=args.past_days)
    hi = today + timedelta(days=args.future_days)

    rows = []
    for i, sym in enumerate(meta, 1):
        if i % 50 == 0 or i == total:
            print(f"    {i}/{total} ...", file=sys.stderr)
        ev = fetch_events(sym)
        if ev.empty:
            time.sleep(args.sleep)
            continue
        for _, e in ev.iterrows():
            if e.get("category") not in cats:
                continue
            # mốc ngày để lọc: ưu tiên record_date, rồi exright_date
            anchor = _date_only(e.get("record_date")) or _date_only(e.get("exright_date"))
            if anchor:
                try:
                    d = datetime.strptime(anchor, "%Y-%m-%d").date()
                    if not (lo <= d <= hi):
                        continue
                except ValueError:
                    pass
            exch, name = meta.get(sym, ("", ""))
            rows.append({
                "ticker": sym,
                "exchange": exch,
                "organ_name": name,
                "category_label": CATEGORY_LABEL.get(e.get("category"), e.get("category")),
                "event_name_vi": e.get("event_name_vi", ""),
                "event_title_vi": e.get("event_title_vi", ""),
                "ty_le": _fmt_ratio(e),
                "value_per_share": "" if pd.isna(e.get("value_per_share")) else e.get("value_per_share"),
                "exright_date": _date_only(e.get("exright_date")),
                "record_date": _date_only(e.get("record_date")),
                "exercise_date": _date_only(e.get("payout_date")) or _date_only(e.get("issue_date")),
                "_sort": anchor or "9999",
            })
        time.sleep(args.sleep)

    df = pd.DataFrame(rows)
    if df.empty:
        print("[!] Không tìm thấy sự kiện nào trong khoảng thời gian đã chọn.", file=sys.stderr)
        # vẫn ghi file rỗng có header để pipeline ổn định
        out = pd.DataFrame(columns=[h for h, _ in OUTPUT_COLUMNS])
    else:
        df = df.sort_values(["_sort", "ticker"]).reset_index(drop=True)
        out = pd.DataFrame({h: df[c] for h, c in OUTPUT_COLUMNS})

    csv_path = "data/lich_su_kien.csv"
    out.to_csv(csv_path, index=False, encoding="utf-8-sig")  # BOM để Excel mở đúng tiếng Việt
    print(f"[✓] Đã ghi {len(out)} dòng -> {csv_path}", file=sys.stderr)
    try:
        out.to_excel("data/lich_su_kien.xlsx", index=False)
        print("[✓] Đã ghi data/lich_su_kien.xlsx", file=sys.stderr)
    except Exception as e:  # openpyxl chưa cài
        print(f"[i] Bỏ qua .xlsx ({e})", file=sys.stderr)

    # ghi mốc cập nhật
    with open("data/last_updated.txt", "w", encoding="utf-8") as f:
        f.write(datetime.now().strftime("Cập nhật: %Y-%m-%d %H:%M") + "\n")
    return out


def main():
    p = argparse.ArgumentParser(description="Lập bảng lịch chốt quyền / cổ tức CK Việt Nam")
    p.add_argument("--symbols", help="Danh sách mã, ngăn cách dấu phẩy (vd HPG,VNM). Mặc định: toàn thị trường")
    p.add_argument("--exchange", help="Lọc theo sàn: HOSE / HNX / UPCOM")
    p.add_argument("--limit", type=int, help="Giới hạn số mã (để test nhanh)")
    p.add_argument("--categories", help="Nhóm sự kiện, mặc định DIVIDEND,SHAREHOLDER_MEETING")
    p.add_argument("--past-days", type=int, default=30, help="Lùi về quá khứ (ngày), mặc định 30")
    p.add_argument("--future-days", type=int, default=180, help="Tới tương lai (ngày), mặc định 180")
    p.add_argument("--sleep", type=float, default=0.2, help="Nghỉ giữa các request (giây)")
    build(p.parse_args())


if __name__ == "__main__":
    main()
