package me.etylix.dlu.ips

import android.os.Build
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    // Engine Flutter chỉ đọc tần số quét chứ không xin, nên nhiều máy (vivo,
    // Xiaomi…) giữ app ở 60 Hz trong khi app Compose chạy 120 Hz. Chọn chế độ
    // màn hình cùng độ phân giải có tần số cao nhất.
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return
        val hienTai = display?.mode ?: return
        val cao = display?.supportedModes
            ?.filter { it.physicalWidth == hienTai.physicalWidth && it.physicalHeight == hienTai.physicalHeight }
            ?.maxByOrNull { it.refreshRate } ?: return
        window.attributes = window.attributes.also { it.preferredDisplayModeId = cao.modeId }
    }
}
