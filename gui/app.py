"""
Desktop GUI — PySide6 (Qt 6) with Discord dark theme.
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
    QGroupBox, QFileDialog, QMenu, QCheckBox, QFormLayout,
)
from PySide6.QtCore import Qt, Signal, Slot, QObject, QThread
from PySide6.QtGui import QPalette, QColor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.discord_client import DiscordSelfClient
from core.server_cloner import ServerCloner
from core.webhook_manager import WebhookManager
from core.mapping_exporter import export_json, export_csv, export_markdown


# ── Workers ─────────────────────────────────────────────────────────────

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
                self.progress.emit("Verifying token...", 0)
                self.progress.emit(f"Logged in as {client.user}", 5)

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
            self.progress.emit("Done!", 100)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()


# ── Dark Palette ────────────────────────────────────────────────────────

def apply_dark_theme(app: QApplication):
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor("#0f0f13"))
    pal.setColor(QPalette.WindowText, QColor("#e4e4ed"))
    pal.setColor(QPalette.Base, QColor("#1a1a24"))
    pal.setColor(QPalette.AlternateBase, QColor("#24243a"))
    pal.setColor(QPalette.Text, QColor("#e4e4ed"))
    pal.setColor(QPalette.Button, QColor("#2e2e48"))
    pal.setColor(QPalette.ButtonText, QColor("#e4e4ed"))
    pal.setColor(QPalette.Highlight, QColor("#5865f2"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.Disabled, QPalette.Text, QColor("#555560"))
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#555560"))
    app.setPalette(pal)
    app.setStyleSheet("""
        QGroupBox { font-weight: bold; border: 1px solid #2e2e48; border-radius: 8px;
            margin-top: 1.2em; padding-top: 1.2em; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #a0a0b8; }
        QLineEdit, QComboBox {
            background: #1a1a24; border: 1px solid #2e2e48; border-radius: 6px;
            padding: 8px 12px; color: #e4e4ed; font-size: 13px; }
        QLineEdit:focus, QComboBox:focus { border-color: #5865f2; }
        QComboBox::drop-down { border: none; width: 24px; }
        QComboBox QAbstractItemView {
            background: #1a1a24; border: 1px solid #2e2e48;
            selection-background-color: #5865f2; color: #e4e4ed; }
        QPushButton {
            background: #5865f2; color: #fff; border: none; border-radius: 6px;
            padding: 8px 18px; font-weight: 600; font-size: 13px; }
        QPushButton:hover { background: #4752c4; }
        QPushButton:disabled { background: #3a3a50; color: #666; }
        QPushButton#btnExport {
            background: #1a1a24; color: #e4e4ed; border: 1px solid #2e2e48; }
        QPushButton#btnExport:hover { background: #2e2e48; }
        QProgressBar {
            border: none; border-radius: 10px; background: #1a1a24; height: 18px;
            text-align: center; font-size: 11px; color: transparent; }
        QProgressBar::chunk {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #5865f2, stop:1 #a855f7);
            border-radius: 10px; }
        QTableWidget {
            background: #1a1a24; alternate-background-color: #1e1e2e;
            gridline-color: #2e2e48; border: 1px solid #2e2e48; border-radius: 6px; font-size: 12px; }
        QTableWidget::item { padding: 4px 8px; }
        QTableWidget::item:selected { background: #5865f2; }
        QHeaderView::section {
            background: #0f0f13; color: #8888a0; font-weight: bold;
            border: none; border-bottom: 1px solid #2e2e48; padding: 6px 8px; }
        QCheckBox { color: #e4e4ed; spacing: 8px; }
        QCheckBox::indicator {
            width: 18px; height: 18px; border: 1px solid #2e2e48; border-radius: 4px;
            background: #1a1a24; }
        QCheckBox::indicator:checked { background: #5865f2; border-color: #5865f2; }
    """)


# ── Main Window ─────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord Server Cloner")
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

        # Title
        title = QLabel("Discord Server Cloner")
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold; padding: 8px 0;"
            "color: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #5865f2, stop:1 #a855f7);"
            "qproperty-alignment: AlignCenter;"
        )
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        sub = QLabel("Clone server structure & webhook mappings")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #8888a0; font-size: 13px; margin-bottom: 4px;")
        main_layout.addWidget(sub)

        # ── Step 1: Token + Proxy ──
        grp_token = QGroupBox("Step 1 — Discord Token & Proxy")
        lyt_token = QVBoxLayout(grp_token)
        lyt_token.setSpacing(8)

        hint = QLabel("Enter your Discord user token. It never leaves your machine.")
        hint.setStyleSheet("color: #8888a0; font-size: 12px; font-weight: normal;")
        lyt_token.addWidget(hint)

        row_token = QHBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Paste your Discord token here...")
        self.btn_verify = QPushButton("Verify & Load Servers")
        self.btn_verify.setFixedWidth(180)
        row_token.addWidget(self.token_input)
        row_token.addWidget(self.btn_verify)
        lyt_token.addLayout(row_token)

        # Proxy row
        row_proxy = QHBoxLayout()
        row_proxy.setSpacing(8)
        self.cb_proxy = QCheckBox("Use Proxy")
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

        # ── Step 2: Server Selection ──
        grp_srv = QGroupBox("Step 2 — Select Servers")
        lyt_srv = QHBoxLayout(grp_srv)
        lyt_srv.setSpacing(12)

        left = QVBoxLayout()
        left.addWidget(QLabel("Source Server (copy FROM)"))
        self.cmb_source = QComboBox()
        self.cmb_source.setPlaceholderText("-- Select source --")
        left.addWidget(self.cmb_source)
        lyt_srv.addLayout(left)

        arrow = QLabel("→")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet("font-size: 24px; color: #5865f2; padding-top: 16px;")
        lyt_srv.addWidget(arrow)

        right = QVBoxLayout()
        right.addWidget(QLabel("Target Server (copy TO)"))
        self.cmb_target = QComboBox()
        self.cmb_target.setPlaceholderText("-- Select target --")
        right.addWidget(self.cmb_target)
        lyt_srv.addLayout(right)

        self.btn_clone = QPushButton("Start Clone")
        self.btn_clone.setEnabled(False)
        self.btn_clone.setFixedWidth(140)
        lyt_srv.addWidget(self.btn_clone)

        main_layout.addWidget(grp_srv)

        # ── Step 3: Progress ──
        self.grp_progress = QGroupBox("Step 3 — Progress")
        self.grp_progress.setVisible(False)
        lyt_prog = QVBoxLayout(self.grp_progress)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(18)
        lyt_prog.addWidget(self.progress_bar)
        self.lbl_progress = QLabel("Waiting...")
        self.lbl_progress.setAlignment(Qt.AlignCenter)
        self.lbl_progress.setStyleSheet("font-size: 12px; color: #8888a0;")
        lyt_prog.addWidget(self.lbl_progress)
        main_layout.addWidget(self.grp_progress)

        # ── Step 4: Results ──
        self.grp_results = QGroupBox("Step 4 — Results & Export")
        self.grp_results.setVisible(False)
        lyt_res = QVBoxLayout(self.grp_results)
        lyt_res.setSpacing(8)

        self.lbl_summary = QLabel("")
        self.lbl_summary.setStyleSheet(
            "font-size: 13px; padding: 8px; background: #1a1a24; border-radius: 6px;"
        )
        lyt_res.addWidget(self.lbl_summary)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        for text, slot in [
            ("Copy JSON", lambda: self._copy_export("json")),
            ("Copy CSV", lambda: self._copy_export("csv")),
            ("Copy Markdown", lambda: self._copy_export("markdown")),
            ("Download .json", lambda: self._download_export("json")),
            ("Download .csv", lambda: self._download_export("csv")),
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
            "Source Channel", "Source Webhook", "Target Channel",
            "Target Webhook", "Type", "Status",
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

        self.statusBar().setStyleSheet("color: #8888a0; font-size: 11px;")
        self.statusBar().showMessage("Ready")

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

    # ── Verify ──

    @Slot()
    def _on_verify(self):
        token = self.token_input.text().strip()
        if not token:
            self._set_verify("Please enter a token.", "red")
            return
        self.token = token
        self.proxy = self._effective_proxy
        self.btn_verify.setEnabled(False)
        self._set_verify("Verifying...", "#faa81a")

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
            f"Logged in as {user} — {len(guilds)} manageable server(s) found.",
            "#3ba55c",
        )
        self.cmb_source.clear()
        self.cmb_target.clear()
        self.cmb_source.addItem("-- Select source --", None)
        self.cmb_target.addItem("-- Select target --", None)
        for g in guilds:
            self.cmb_source.addItem(g["name"], g["id"])
            self.cmb_target.addItem(g["name"], g["id"])

    @Slot(str)
    def _on_verify_error(self, err: str):
        self.btn_verify.setEnabled(True)
        self._set_verify(f"Error: {err}", "#ed4245")

    def _set_verify(self, text: str, color: str):
        self.lbl_verify_status.setText(text)
        self.lbl_verify_status.setStyleSheet(f"font-size: 12px; color: {color};")

    @Slot()
    def _on_server_changed(self):
        self.btn_clone.setEnabled(
            bool(self.cmb_source.currentData() and self.cmb_target.currentData())
        )

    # ── Clone ──

    @Slot()
    def _on_clone(self):
        src = self.cmb_source.currentData()
        tgt = self.cmb_target.currentData()
        if src == tgt:
            QMessageBox.warning(self, "Invalid", "Source and target servers must be different.")
            return

        self.btn_clone.setEnabled(False)
        self.btn_verify.setEnabled(False)
        self.grp_progress.setVisible(True)
        self.grp_results.setVisible(False)
        self.progress_bar.setValue(0)
        self.lbl_progress.setText("Starting...")
        self.statusBar().showMessage("Cloning...")

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
        self.statusBar().showMessage("Clone complete!")

    @Slot(str)
    def _on_clone_error(self, err: str):
        self.btn_clone.setEnabled(True)
        self.btn_verify.setEnabled(True)
        self.grp_progress.setVisible(False)
        QMessageBox.critical(self, "Clone Failed", err)
        self.statusBar().showMessage("Clone failed")

    # ── Results ──

    def _populate_results(self, mapping: dict):
        entries = list(mapping.values())
        ok = sum(1 for e in entries if not e.get("error"))
        err_count = sum(1 for e in entries if e.get("error"))
        self.lbl_summary.setText(f"Total: <span style='color:#3ba55c;'>{len(entries)}</span> | "
                                 f"OK: <span style='color:#3ba55c;'>{ok}</span> | "
                                 f"Failed: <span style='color:#ed4245;'>{err_count}</span>")

        self.table.setRowCount(len(entries))
        for row, (_cid, info) in enumerate(mapping.items()):
            status = "OK" if not info.get("error") else f"ERROR: {info['error']}"
            cells = [
                info.get("source_name", "N/A"),
                (info.get("source_webhook_url") or "N/A")[:60],
                info.get("target_name") or "FAILED",
                (info.get("target_webhook_url") or "N/A")[:60],
                info.get("type", "?"),
                status,
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()

    # ── Export ──

    def _copy_export(self, fmt: str):
        if not self.mapping:
            return
        text = {"json": export_json, "csv": export_csv, "markdown": export_markdown}[fmt](self.mapping)
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage(f"{fmt.upper()} copied to clipboard!")

    def _download_export(self, fmt: str):
        if not self.mapping:
            return
        ext = "md" if fmt == "markdown" else fmt
        text = {"json": export_json, "csv": export_csv, "markdown": export_markdown}[fmt](self.mapping)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Mapping", f"discord-channel-mapping.{ext}", f"*.{ext}"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.statusBar().showMessage(f"Saved to {path}")

    # ── Table context menu ──

    def _table_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #1a1a24; border: 1px solid #2e2e48; color: #e4e4ed; padding: 4px; }
            QMenu::item { padding: 6px 24px; }
            QMenu::item:selected { background: #5865f2; }
        """)
        copy_row = menu.addAction("Copy Row as JSON")
        action = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if action == copy_row:
            row = self.table.currentRow()
            if row >= 0:
                data = {
                    "source_channel": self.table.item(row, 0).text(),
                    "source_webhook": self.table.item(row, 1).text(),
                    "target_channel": self.table.item(row, 2).text(),
                    "target_webhook": self.table.item(row, 3).text(),
                    "type": self.table.item(row, 4).text(),
                    "status": self.table.item(row, 5).text(),
                }
                QApplication.clipboard().setText(json.dumps(data, indent=2))
                self.statusBar().showMessage("Row copied!")


def main():
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()())


if __name__ == "__main__":
    main()
