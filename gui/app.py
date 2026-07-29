"""
桌面 GUI — PySide6 (Qt 6) 浅色主题。
"""
import sys
import os
import asyncio
import json
import threading
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QFileDialog, QMenu, QCheckBox, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, Slot, QObject, QThread
from PySide6.QtGui import QPalette, QColor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.discord_client import DiscordSelfClient
from core.server_cloner import ServerCloner
from core.webhook_manager import WebhookManager
from core.mapping_exporter import export_json, export_csv, export_markdown


# ── 工作线程 ─────────────────────────────────────────────────────────────

class VerifyWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, token: str, proxy: Optional[str]):
        super().__init__()
        self.token = token
        self.proxy = proxy

    def run(self):
        async def _verify():
            async with DiscordSelfClient(self.token, proxy=self.proxy) as client:
                user = client.user
                guilds = await client.get_manageable_guilds()
                return {
                    "user": str(user),
                    "guilds": [{"id": str(g.id), "name": g.name} for g in guilds],
                }
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_verify())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()


class CloneWorker(QObject):
    progress = Signal(str, int)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, token: str, proxy: Optional[str], source_id: str, target_id: str):
        super().__init__()
        self.token = token
        self.proxy = proxy
        self.source_id = source_id
        self.target_id = target_id

    def run(self):
        async def _clone():
            async with DiscordSelfClient(self.token, proxy=self.proxy) as client:
                self.progress.emit("正在验证 Token...", 0)
                self.progress.emit(f"已登录：{client.user}", 5)

                cloner = ServerCloner(client, progress_cb=lambda m, p: self.progress.emit(m, p))
                mapping = await cloner.clone(
                    int(self.source_id), int(self.target_id)
                )

                wh = WebhookManager(client, progress_cb=lambda m, p: self.progress.emit(m, p))
                mapping = await wh.setup_webhooks(mapping)
                return mapping

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_clone())
            self.progress.emit("完成！", 100)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()


# ── 浅色主题 ─────────────────────────────────────────────────────────────

def apply_light_theme(app: QApplication):
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor("#f5f5f8"))
    pal.setColor(QPalette.WindowText, QColor("#1a1a2e"))
    pal.setColor(QPalette.Base, QColor("#ffffff"))
    pal.setColor(QPalette.AlternateBase, QColor("#f0f0f5"))
    pal.setColor(QPalette.Text, QColor("#1a1a2e"))
    pal.setColor(QPalette.Button, QColor("#e8e8f0"))
    pal.setColor(QPalette.ButtonText, QColor("#1a1a2e"))
    pal.setColor(QPalette.Highlight, QColor("#5865f2"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor("#9999a8"))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#9999a8"))
    app.setPalette(pal)
    app.setStyleSheet("""
        QGroupBox { font-weight: bold; border: 1px solid #d4d4dc; border-radius: 8px;
            margin-top: 1.2em; padding-top: 1.2em; background: #ffffff; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #5865f2; }
        QLineEdit, QComboBox {
            background: #ffffff; border: 1px solid #d4d4dc; border-radius: 6px;
            padding: 8px 12px; color: #1a1a2e; font-size: 13px; }
        QLineEdit:focus, QComboBox:focus { border-color: #5865f2; }
        QComboBox::drop-down { border: none; width: 24px; }
        QComboBox QAbstractItemView {
            background: #ffffff; border: 1px solid #d4d4dc;
            selection-background-color: #5865f2; color: #1a1a2e; }
        QPushButton {
            background: #5865f2; color: #fff; border: none; border-radius: 6px;
            padding: 8px 18px; font-weight: 600; font-size: 13px; }
        QPushButton:hover { background: #4752c4; }
        QPushButton:disabled { background: #d4d4dc; color: #9999a8; }
        QPushButton#btnExport {
            background: #ffffff; color: #1a1a2e; border: 1px solid #d4d4dc; }
        QPushButton#btnExport:hover { background: #e8e8f0; }
        QProgressBar {
            border: none; border-radius: 10px; background: #e8e8f0; height: 18px;
            text-align: center; font-size: 11px; color: transparent; }
        QProgressBar::chunk {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #5865f2, stop:1 #a855f7);
            border-radius: 10px; }
        QTableWidget {
            background: #ffffff; alternate-background-color: #f8f8fc;
            gridline-color: #e8e8f0; border: 1px solid #d4d4dc; border-radius: 6px; font-size: 12px; }
        QTableWidget::item { padding: 4px 8px; }
        QTableWidget::item:selected { background: #5865f2; color: #ffffff; }
        QHeaderView::section {
            background: #f5f5f8; color: #666680; font-weight: bold;
            border: none; border-bottom: 1px solid #d4d4dc; padding: 6px 8px; }
        QCheckBox { color: #1a1a2e; spacing: 8px; }
        QCheckBox::indicator {
            width: 18px; height: 18px; border: 1px solid #d4d4dc; border-radius: 4px;
            background: #ffffff; }
        QCheckBox::indicator:checked { background: #5865f2; border-color: #5865f2; }
    """)


# ── 主窗口 ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord 服务器克隆工具")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.resize(980, 760)
        self.setMinimumSize(820, 600)

        self.token: Optional[str] = None
        self.proxy: Optional[str] = None
        self.mapping: Optional[dict] = None

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ── 步骤 1：Token 与代理 ──
        grp_token = QGroupBox("步骤 1 — Discord Token 与代理")
        grp_token.setSizePolicy(grp_token.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
        lyt_token = QVBoxLayout(grp_token)
        lyt_token.setSpacing(8)

        hint = QLabel("输入你的 Discord 用户 Token，它不会离开你的电脑。")
        hint.setStyleSheet("color: #8888a0; font-size: 12px; font-weight: normal;")
        lyt_token.addWidget(hint)

        row_token = QHBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("在此粘贴 Discord Token...")
        self.btn_verify = QPushButton("验证并加载服务器")
        self.btn_verify.setFixedWidth(180)
        row_token.addWidget(self.token_input)
        row_token.addWidget(self.btn_verify)
        lyt_token.addLayout(row_token)

        # 代理行
        row_proxy = QHBoxLayout()
        row_proxy.setSpacing(8)
        self.cb_proxy = QCheckBox("使用代理")
        self.cb_proxy.setChecked(True)
        self.cb_proxy.setStyleSheet("font-weight: normal;")
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:7897")
        self.proxy_input.setText("http://127.0.0.1:7897")
        self.proxy_input.setMaximumWidth(280)
        self.cb_proxy.toggled.connect(lambda v: self.proxy_input.setEnabled(v))
        row_proxy.addWidget(self.cb_proxy)
        row_proxy.addWidget(self.proxy_input)
        row_proxy.addStretch()
        lyt_token.addLayout(row_proxy)

        self.lbl_verify_status = QLabel("")
        self.lbl_verify_status.setStyleSheet("font-size: 12px;")
        lyt_token.addWidget(self.lbl_verify_status)

        main_layout.addWidget(grp_token)

        # ── 步骤 2：选择服务器 ──
        grp_srv = QGroupBox("步骤 2 — 选择服务器")
        grp_srv.setSizePolicy(grp_srv.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
        lyt_srv = QHBoxLayout(grp_srv)
        lyt_srv.setSpacing(12)

        left = QVBoxLayout()
        left.addWidget(QLabel("源服务器（从这里复制）"))
        self.cmb_source = QComboBox()
        self.cmb_source.setPlaceholderText("-- 选择源服务器 --")
        left.addWidget(self.cmb_source)
        lyt_srv.addLayout(left)

        arrow = QLabel("→")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet("font-size: 24px; color: #5865f2; padding-top: 16px;")
        lyt_srv.addWidget(arrow)

        right = QVBoxLayout()
        right.addWidget(QLabel("目标服务器（复制到这里）"))
        self.cmb_target = QComboBox()
        self.cmb_target.setPlaceholderText("-- 选择目标服务器 --")
        right.addWidget(self.cmb_target)
        lyt_srv.addLayout(right)

        self.btn_clone = QPushButton("开始克隆")
        self.btn_clone.setEnabled(False)
        self.btn_clone.setFixedWidth(140)
        lyt_srv.addWidget(self.btn_clone)

        main_layout.addWidget(grp_srv)

        # ── 步骤 3：进度 ──
        self.grp_progress = QGroupBox("步骤 3 — 进度")
        self.grp_progress.setSizePolicy(self.grp_progress.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
        self.grp_progress.setVisible(False)
        lyt_prog = QVBoxLayout(self.grp_progress)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(18)
        lyt_prog.addWidget(self.progress_bar)
        self.lbl_progress = QLabel("等待中...")
        self.lbl_progress.setAlignment(Qt.AlignCenter)
        self.lbl_progress.setStyleSheet("font-size: 12px; color: #8888a0;")
        lyt_prog.addWidget(self.lbl_progress)
        main_layout.addWidget(self.grp_progress)

        # ── 步骤 4：结果与导出 ──
        self.grp_results = QGroupBox("步骤 4 — 结果与导出")
        self.grp_results.setSizePolicy(self.grp_results.sizePolicy().horizontalPolicy(), QSizePolicy.Preferred)
        self.grp_results.setVisible(False)
        lyt_res = QVBoxLayout(self.grp_results)
        lyt_res.setSpacing(8)

        self.lbl_summary = QLabel("")
        self.lbl_summary.setStyleSheet(
            "font-size: 13px; padding: 8px; background: #f5f5f8; border-radius: 6px;"
        )
        lyt_res.addWidget(self.lbl_summary)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        for text, slot in [
            ("复制 JSON", lambda: self._copy_export("json")),
            ("复制 CSV", lambda: self._copy_export("csv")),
            ("复制 Markdown", lambda: self._copy_export("markdown")),
            ("下载 .json", lambda: self._download_export("json")),
            ("下载 .csv", lambda: self._download_export("csv")),
        ]:
            btn = QPushButton(text)
            btn.setObjectName("btnExport")
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        btn_row.addStretch()
        lyt_res.addLayout(btn_row)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "源频道", "源 Webhook", "目标频道",
            "目标 Webhook", "类型", "状态",
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._table_menu)
        lyt_res.addWidget(self.table)

        main_layout.addWidget(self.grp_results)
        main_layout.addStretch()

        self.statusBar().setStyleSheet("color: #8888a0; font-size: 11px;")
        self.statusBar().showMessage("就绪")

    def _connect_signals(self):
        self.btn_verify.clicked.connect(self._on_verify)
        self.cmb_source.currentIndexChanged.connect(self._on_server_changed)
        self.cmb_target.currentIndexChanged.connect(self._on_server_changed)
        self.btn_clone.clicked.connect(self._on_clone)

    @property
    def _effective_proxy(self) -> Optional[str]:
        if not self.cb_proxy.isChecked():
            return None
        p = self.proxy_input.text().strip()
        return p if p else "http://127.0.0.1:7897"

    # ── 验证 ──

    @Slot()
    def _on_verify(self):
        token = self.token_input.text().strip()
        if not token:
            self._set_verify("请输入 Token。", "#ed4245")
            return
        self.token = token
        self.proxy = self._effective_proxy
        self.btn_verify.setEnabled(False)
        self._set_verify("正在验证...", "#faa81a")

        self.verify_worker = VerifyWorker(token, self.proxy)
        self.verify_thread = QThread()
        self.verify_worker.moveToThread(self.verify_thread)
        self.verify_thread.started.connect(self.verify_worker.run)
        self.verify_worker.finished.connect(self._on_verify_done)
        self.verify_worker.error.connect(self._on_verify_error)
        self.verify_worker.finished.connect(self.verify_thread.quit)
        self.verify_worker.error.connect(self.verify_thread.quit)
        self.verify_thread.start()

    @Slot(dict)
    def _on_verify_done(self, data: dict):
        self.btn_verify.setEnabled(True)
        user = data["user"]
        guilds = data["guilds"]
        self._set_verify(
            f"已登录：{user} — 找到 {len(guilds)} 个服务器。",
            "#3ba55c",
        )
        self.cmb_source.clear()
        self.cmb_target.clear()
        self.cmb_source.addItem("-- 选择源服务器 --", None)
        self.cmb_target.addItem("-- 选择目标服务器 --", None)
        for g in guilds:
            self.cmb_source.addItem(g["name"], g["id"])
            self.cmb_target.addItem(g["name"], g["id"])

    @Slot(str)
    def _on_verify_error(self, err: str):
        self.btn_verify.setEnabled(True)
        self._set_verify(f"错误：{err}", "#ed4245")

    def _set_verify(self, text: str, color: str):
        self.lbl_verify_status.setText(text)
        self.lbl_verify_status.setStyleSheet(f"font-size: 12px; color: {color};")

    @Slot()
    def _on_server_changed(self):
        self.btn_clone.setEnabled(
            bool(self.cmb_source.currentData() and self.cmb_target.currentData())
        )

    # ── 克隆 ──

    @Slot()
    def _on_clone(self):
        src = self.cmb_source.currentData()
        tgt = self.cmb_target.currentData()
        if src == tgt:
            QMessageBox.warning(self, "参数错误", "源服务器和目标服务器不能相同。")
            return

        self.btn_clone.setEnabled(False)
        self.btn_verify.setEnabled(False)
        self.grp_progress.setVisible(True)
        self.grp_results.setVisible(False)
        self.progress_bar.setValue(0)
        self.lbl_progress.setText("启动中...")
        self.statusBar().showMessage("正在克隆...")

        self.clone_worker = CloneWorker(self.token, self.proxy, src, tgt)
        self.clone_thread = QThread()
        self.clone_worker.moveToThread(self.clone_thread)
        self.clone_thread.started.connect(self.clone_worker.run)
        self.clone_worker.progress.connect(self._on_progress)
        self.clone_worker.finished.connect(self._on_clone_done)
        self.clone_worker.error.connect(self._on_clone_error)
        self.clone_worker.finished.connect(self.clone_thread.quit)
        self.clone_worker.error.connect(self.clone_thread.quit)
        self.clone_thread.start()

    @Slot(str, int)
    def _on_progress(self, msg: str, pct: int):
        self.progress_bar.setValue(pct)
        self.lbl_progress.setText(msg)

    @Slot(dict)
    def _on_clone_done(self, mapping: dict):
        self.mapping = mapping
        self.btn_clone.setEnabled(True)
        self.btn_verify.setEnabled(True)
        self.grp_progress.setVisible(False)
        self.grp_results.setVisible(True)
        self._populate_results(mapping)
        self.statusBar().showMessage("克隆完成！")

    @Slot(str)
    def _on_clone_error(self, err: str):
        self.btn_clone.setEnabled(True)
        self.btn_verify.setEnabled(True)
        self.grp_progress.setVisible(False)
        QMessageBox.critical(self, "克隆失败", err)
        self.statusBar().showMessage("克隆失败")

    # ── 结果 ──

    def _populate_results(self, mapping: dict):
        entries = list(mapping.values())
        ok = sum(1 for e in entries if not e.get("error"))
        err_count = sum(1 for e in entries if e.get("error"))
        self.lbl_summary.setText(f"总计：<span style='color:#3ba55c;'>{len(entries)}</span> | "
                                 f"成功：<span style='color:#3ba55c;'>{ok}</span> | "
                                 f"失败：<span style='color:#ed4245;'>{err_count}</span>")

        self.table.setRowCount(len(entries))
        for row, (_cid, info) in enumerate(mapping.items()):
            status = "成功" if not info.get("error") else f"错误：{info['error']}"
            cells = [
                info.get("source_name", "未知"),
                (info.get("source_webhook_url") or "未知")[:60],
                info.get("target_name") or "失败",
                (info.get("target_webhook_url") or "未知")[:60],
                info.get("type", "?"),
                status,
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()

    # ── 导出 ──

    def _copy_export(self, fmt: str):
        if not self.mapping:
            return
        text = {"json": export_json, "csv": export_csv, "markdown": export_markdown}[fmt](self.mapping)
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage(f"{fmt.upper()} 已复制到剪贴板！")

    def _download_export(self, fmt: str):
        if not self.mapping:
            return
        ext = "md" if fmt == "markdown" else fmt
        text = {"json": export_json, "csv": export_csv, "markdown": export_markdown}[fmt](self.mapping)
        path, _ = QFileDialog.getSaveFileName(
            self, "保存映射文件", f"discord-channel-mapping.{ext}", f"*.{ext}"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.statusBar().showMessage(f"已保存到 {path}")

    # ── 表格右键菜单 ──

    def _table_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #ffffff; border: 1px solid #d4d4dc; color: #1a1a2e; padding: 4px; }
            QMenu::item { padding: 6px 24px; }
            QMenu::item:selected { background: #5865f2; color: #ffffff; }
        """)
        copy_row = menu.addAction("复制当前行为 JSON")
        action = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if action == copy_row:
            row = self.table.currentRow()
            if row >= 0:
                data = {
                    "源频道": self.table.item(row, 0).text(),
                    "源 Webhook": self.table.item(row, 1).text(),
                    "目标频道": self.table.item(row, 2).text(),
                    "目标 Webhook": self.table.item(row, 3).text(),
                    "类型": self.table.item(row, 4).text(),
                    "状态": self.table.item(row, 5).text(),
                }
                QApplication.clipboard().setText(json.dumps(data, indent=2, ensure_ascii=False))
                self.statusBar().showMessage("当前行已复制！")


def main():
    app = QApplication(sys.argv)
    apply_light_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()())


if __name__ == "__main__":
    main()
