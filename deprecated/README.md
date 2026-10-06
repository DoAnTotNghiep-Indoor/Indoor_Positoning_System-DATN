# deprecated

Mã và tài liệu cũ đã có bản thay thế. Giữ lại để tham khảo khi viết báo cáo; mã ở đây không chạy.

| Nội dung | Thay bằng |
|---|---|
| `notebooks/` — tiền xử lý và train trên Google Colab (12 bước `colab_steps/`, 2 notebook) | `ml/preprocess.py`, `ml/train.py`, chạy bằng `python -m ml.pipeline` |
| `notebooks/tools/layout_tool_click_toado.py` — bấm lên ảnh sơ đồ để lấy toạ độ RP | `data/reference/reference_points.csv`, sơ đồ `data/reference/mat_bang_tang1.yaml` |
| `tools/trich_ban_do.py` — dò tường, vật cản từ `Map.png` của CTK45 ra lưới đi lại, kèm 15 cửa giả định và luật nối tay; `tools/ve_ban_ve.py`, `tools/ban_do_di_do.py` — hình báo cáo vẽ trên `Map.png` (`reports/figures/ban_ve_*.png`, `ban_do_di_do.png`, `do_thi_di_lai.png`) | `tools/luoi_di_lai.py` dựng lưới đi lại từ sơ đồ đếm gạch `mat_bang_tang1.yaml` |
| `tai_lieu/Phan_Tich_Thiet_Ke_He_Thong.md` — phân tích thiết kế viết dần trong quá trình làm, kèm đề xuất ban đầu, đối chiếu và số đo chi tiết (tỉ lệ mét, phương vị, so sánh mô hình) | `docs/thiet_ke_he_thong.md` |
