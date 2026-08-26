# Audit UX/UI mobile

Ngày rà soát: 26/08/2026  
Phạm vi: toàn bộ `mobile/lib` và các widget test của ứng dụng Flutter IPS DLU.

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
| Thấp | Header bản đồ và placeholder ảnh vẫn là dữ liệu demo | Giữ nguyên trong phạm vi demo; cần thay bằng dữ liệu API/ảnh thật ở giai đoạn tích hợp backend |

## Hướng tối ưu UX/UI tiếp theo

1. **P0 — Kiểm thử trực quan trên thiết bị thật.** Chụp/đối chiếu Home, Map, Search và Detail ở Android nhỏ (360dp), máy có notch, gesture navigation và text scale 1.3–2.0. Widget test bắt được overflow logic nhưng không thay thế đánh giá khoảng cách, độ tương phản và cảm giác chạm.
2. **P0 — Hoàn thiện luồng định vị.** Khi API sẵn sàng, hiển thị trạng thái đang định vị/mất tín hiệu/độ chính xác thấp và cho phép retry; nút “Định vị lại” hiện đang chỉ hiện toast demo.
3. **P1 — Làm rõ tìm kiếm.** Debounce khi gọi API, hiển thị loading/error/retry, giữ query khi đổi filter và thêm nút xoá query riêng nếu bàn phím đang mở.
4. **P1 — Làm cho sơ đồ có tính dẫn đường.** Cho phép chạm phòng để mở đúng dữ liệu phòng, hiển thị legend và trạng thái tầng; khi zoom nên có affordance reset/recenter rõ ràng.
5. **P1 — Lưu cài đặt.** Lưu theme, locale và tuỳ chọn định vị bằng storage; đồng bộ trạng thái quyền thật với OS thay vì giá trị demo.
6. **P2 — Hiệu năng và giảm chuyển động.** Đo shader/liquid glass trên máy cấp thấp, giảm blur khi cần và tôn trọng `MediaQuery.disableAnimations`/tuỳ chọn giảm chuyển động.
7. **P2 — Bản địa hoá sản phẩm thật.** Đưa tên khu vực, category và nội dung chi tiết về API theo locale; kiểm tra pluralization và thuật ngữ song ngữ với người dùng DLU.

## Validation

Chạy từ `mobile/`:

- `D:\flutter\bin\flutter.bat analyze` — `No issues found!`.
- `D:\flutter\bin\flutter.bat test` — tất cả test pass, gồm các test UX/UI mới trong `test/uxui_test.dart`.

Giới hạn: chưa thực hiện visual QA trên thiết bị Android vật lý trong lần rà soát này; kết quả hiện tại là static review và widget test trên Flutter test environment.
