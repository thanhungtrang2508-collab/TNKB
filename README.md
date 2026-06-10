# TNKB — Lịch chốt quyền & cổ tức cổ phiếu Việt Nam

Tự động lập **bảng theo dõi lịch sự kiện quyền** của cổ phiếu niêm yết Việt Nam:
khi nào **chốt quyền**, **chia cổ tức** (tiền mặt / cổ phiếu), **tỷ lệ / số tiền cụ thể**,
và các mốc **ngày tháng**.

## Bảng có gì

Mỗi dòng là một sự kiện quyền của một mã:

| Cột | Ý nghĩa |
|---|---|
| Mã CP | Mã cổ phiếu |
| Sàn | HOSE / HNX / UPCOM |
| Tên DN | Tên doanh nghiệp |
| Nhóm | Cổ tức/Phát hành · ĐHĐCĐ · ... |
| Loại sự kiện | VD: Trả cổ tức bằng tiền mặt / bằng cổ phiếu |
| Chi tiết | Mô tả kèm tỷ lệ |
| Tỷ lệ | VD: 10% |
| Tiền mặt (đ/cp) | Số tiền mặt mỗi cổ phiếu |
| **Ngày GDKHQ** | Giao dịch không hưởng quyền — *mốc canh mua/bán* |
| **Ngày ĐKCC (chốt quyền)** | Ngày đăng ký cuối cùng |
| Ngày thực hiện | Ngày trả tiền / về cổ phiếu |

> 💡 Muốn **được hưởng quyền**, bạn phải sở hữu cổ phiếu **trước ngày GDKHQ**
> (mua chậm nhất vào phiên liền trước ngày GDKHQ).

Đầu ra nằm trong thư mục [`data/`](data/):
- `lich_su_kien.csv` (UTF‑8 có BOM — mở thẳng bằng Excel không lỗi tiếng Việt)
- `lich_su_kien.xlsx`
- `last_updated.txt`

## 📱 Web app theo dõi

Ngoài file Excel/CSV, repo tự build **web app 1 trang** tại [`docs/index.html`](docs/index.html):
- Tab theo sàn (Tất cả / HOSE / HNX / UPCOM) + danh mục yêu thích ⭐ (lưu trên máy)
- Thanh tìm kiếm: gõ mã → hiện ngay thẻ chi tiết đầy đủ sự kiện
- Bộ lọc nhanh (sắp chốt quyền, cổ tức tiền mặt, cổ tức CP, ĐHĐCĐ), sắp xếp theo cột
- Lịch tháng 📅: ngày nào có sự kiện chốt quyền sẽ đánh dấu, bấm vào xem
- Mã màu: 🔺 tăng / 🔻 giảm so kỳ cổ tức trước, vàng = sắp đến ngày GDKHQ

App được build lại mỗi ngày cùng dữ liệu (`scripts/build_app.py`) và deploy lên
GitHub Pages qua [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml)
(yêu cầu repo public). Cũng có thể tải `docs/index.html` về mở trực tiếp bằng trình duyệt.

## Nguồn dữ liệu

Lấy từ thư viện mã nguồn mở [`vnstock`](https://github.com/vnstock-hq) (nguồn VCI).

Giới hạn tốc độ API theo gói:
- **Guest** (không key): 20 request/phút → quét toàn thị trường ~2,5–3 giờ.
- **Community** (có API key miễn phí): 60 request/phút → ~1 giờ.

Để dùng gói Community, đặt API key vào biến môi trường `VNSTOCK_API_KEY`
(lấy key miễn phí tại https://vnstocks.com/login). Trong GitHub Actions, key được
nạp từ **secret** `VNSTOCK_API_KEY` — **không** lưu trong mã nguồn.

```bash
# chạy tay với API key (gói Community, nhanh hơn)
export VNSTOCK_API_KEY="vnstock_xxx"
python3 scripts/build_events.py --sleep 2.5
```

## Chạy tay

```bash
pip install -r requirements.txt

# Toàn thị trường
python3 scripts/build_events.py

# Một danh mục theo dõi riêng
python3 scripts/build_events.py --symbols HPG,VNM,FPT,MWG

# Chỉ một sàn, giới hạn để test nhanh
python3 scripts/build_events.py --exchange HOSE --limit 50

# Tuỳ chỉnh khoảng thời gian
python3 scripts/build_events.py --past-days 30 --future-days 120
```

## Tự động cập nhật

Workflow [`.github/workflows/update-events.yml`](.github/workflows/update-events.yml)
chạy **hằng ngày 08:00 giờ VN** (và chạy tay qua nút *Run workflow*), tự cập nhật
bảng và commit lại vào repo.

> Lịch tự động chỉ kích hoạt khi workflow đã được merge vào nhánh mặc định của repo.

## Miễn trừ trách nhiệm

Dữ liệu lấy tự động từ nguồn công khai, **chỉ để tham khảo**, có thể sai/thiếu/chậm
so với công bố chính thức. Luôn đối chiếu với công bố của doanh nghiệp, Sở GDCK
(HOSE/HNX) và VSDC trước khi ra quyết định đầu tư.
