# Audit UX/UI mobile

Ngày rà soát: 26/08/2026  
Phạm vi: toàn bộ `mobile/lib` và các widget test của ứng dụng Flutter IPS DLU.

> **Trạng thái tính tới 01/09/2026.** Đây là biên bản của đợt rà soát ngày
> 26/08, giữ nguyên làm dấu vết. Bảy hướng tối ưu ở cuối đã làm xong sáu; tình
> trạng từng mục ghi ngay trong danh sách đó.

## Phạm vi đã kiểm tra

| Khu vực | Nội dung đã rà soát |
| --- | --- |
| Trang chủ | Vị trí hiện tại, truy cập nhanh, danh sách gần bạn, khoảng cách và khả năng chạm |
| Bản đồ | Header, nút định vị, thao tác pinch/drag, vùng an toàn và phần bị che bởi bottom navigation |
| Tìm kiếm | Ô nhập trong bottom bar, chip lọc, đếm kết quả, trạng thái rỗng và điều hướng tới chi tiết |
| Chi tiết khu vực | Nút quay lại, bottom sheet cuộn được, CTA, nội dung song ngữ và vùng an toàn cuối màn hình |
| Cài đặt | Nhóm thiết lập, segmented control, switch, theme sáng/tối và đổi ngôn ngữ |
| Thành phần chung | Liquid glass card, nền blob, theme/màu, kích thước vùng chạm, semantics và localization |

## Phát hiện và thay đổi đã thực hiện

| Mức độ | Phát hiện | Xử lý |
| --- | --- | --- |
| Cao | Thẻ/dòng khu vực dùng `GestureDetector` trần nên không có phản hồi khi chạm và thiếu semantics rõ ràng | Thêm `TapFeedback`, trạng thái nhấn nhẹ, nhãn/gợi ý cho trình đọc màn hình và dùng cho card/dòng/CTA |
| Cao | Bottom sheet Chi tiết có thể cao hơn viewport thấp, làm ảnh và CTA nằm ngoài vùng có thể cuộn; thiếu nút quay lại trực quan | Giới hạn chiều cao sheet theo viewport, bọc nội dung bằng `SingleChildScrollView`, thêm nút back 48dp và chừa safe-area cuối màn hình |
| Cao | Tìm kiếm không có trạng thái hướng dẫn khi không có kết quả; bộ lọc có thể làm người dùng không biết nguyên nhân | Thêm empty state có icon, thông điệp, hướng dẫn và nút bỏ bộ lọc; test đường đi này bằng widget test |
| Cao | Bộ lọc so sánh nhãn tiếng Việt cố định với dữ liệu nên sai khi đổi sang English | Đổi sang mã nhóm ổn định (`AreaCategory`) và dịch nhãn hiển thị theo locale |
| Trung bình | Nhiều chuỗi ghép cứng, tên địa điểm chỉ có một ngôn ngữ và số thập phân không theo locale | Bổ sung bản dịch dữ liệu demo, format accuracy theo locale, tách các chuỗi đếm/khoảng cách vào l10n |
| Trung bình | Một số vùng chạm/chip thấp hơn khuyến nghị trên mobile; text scale lớn có nguy cơ cắt nội dung | Nâng chiều cao chip/vùng thao tác, thêm ellipsis có chủ đích và các metric co giãn theo text scale |
| Trung bình | Nút/icon và sơ đồ chưa cung cấp đủ ngữ cảnh cho công nghệ hỗ trợ | Thêm semantic label/hint cho nút định vị, sơ đồ, tiêu đề nhóm và các card tương tác |
| Thấp | Header bản đồ và placeholder ảnh vẫn là dữ liệu demo | ✅ Đã xong. Header đếm khu vực thật và hiện mốc cập nhật thật; ô ảnh thay bằng 38 ảnh chụp tại thư viện |

## Hướng tối ưu UX/UI tiếp theo

1. ⏳ **P0 — Kiểm thử trực quan trên thiết bị thật.** Chụp/đối chiếu Home, Map, Search và Detail ở Android nhỏ (360dp), máy có notch, gesture navigation và text scale 1.3–2.0. Widget test bắt được overflow logic nhưng không thay thế đánh giá khoảng cách, độ tương phản và cảm giác chạm.
2. ✅ **P0 — Hoàn thiện luồng định vị.** Đã xong: quét WiFi thật mỗi 5 giây, phân biệt sáu loại lỗi API và năm lý do không quét được, nút "Định vị lại" bật lại vòng quét thật. Thiếu dữ liệu thì nói "chưa xác định vị trí" chứ không giữ toạ độ cũ.
3. ✅ **P1 — Làm rõ tìm kiếm.** Đã xong phần cốt lõi: tìm trên danh sách khu vực đã có sẵn trong bộ nhớ nên không cần debounce hay trạng thái loading. Query giữ nguyên khi đổi filter.
4. ✅ **P1 — Làm cho sơ đồ có tính dẫn đường.** Đã xong: sơ đồ là bản số hoá thật, chạm vào mở tấm tóm tắt rồi dẫn sang màn Chi tiết đúng khu vực. Còn thiếu: vẽ tuyến chỉ đường lên chính sơ đồ.
5. ✅ **P1 — Lưu cài đặt.** Đã xong: theme, ngôn ngữ và địa chỉ máy chủ lưu bằng `shared_preferences`; dòng quyền đọc trạng thái thật từ hệ điều hành và phân biệt chưa cấp / bị chặn.
6. ⏳ **P2 — Hiệu năng và giảm chuyển động.** Đo shader/liquid glass trên máy cấp thấp, giảm blur khi cần và tôn trọng `MediaQuery.disableAnimations`/tuỳ chọn giảm chuyển động.
7. ✅ **P2 — Bản địa hoá sản phẩm thật.** Tên khu vực và mô tả nay lấy từ `GET /map` chứ không viết cứng trong app. Chưa làm: bản dịch tiếng Anh cho tên khu vực — dữ liệu nguồn chỉ có tiếng Việt.

## Validation

Chạy từ `mobile/`:

- `D:\flutter\bin\flutter.bat analyze` — `No issues found!`.
- `D:\flutter\bin\flutter.bat test` — tất cả test pass, gồm các test UX/UI mới trong `test/uxui_test.dart`.

Giới hạn: chưa thực hiện visual QA trên thiết bị Android vật lý trong lần rà soát này; kết quả hiện tại là static review và widget test trên Flutter test environment.

**Bổ sung 01/09/2026.** Đã chạy trên máy Android thật và bắt được một lỗi mà
widget test không thể thấy: đứng ngoài thư viện, điện thoại nhìn thấy 23 access
point nhưng khớp 0 với hợp đồng dữ liệu, mà ứng dụng vẫn khẳng định người dùng
đang ở "TV3,4" trong thư viện. Đã sửa ở cả hai tầng — máy chủ trả 422, ứng dụng
xoá toạ độ cũ. Vẫn chưa chụp ảnh màn hình bộ giao diện mới trên thiết bị.
