"""
Export channel → webhook mapping to JSON, CSV, or Markdown.
"""
import csv
import json
import io
from typing import Optional


def export_json(mapping: dict[str, dict], indent: int = 2) -> str:
    """Export mapping as formatted JSON."""
    export_data = []
    for source_id, info in mapping.items():
        export_data.append({
            "source_channel_id": source_id,
            "source_channel_name": info.get("source_name", ""),
            "source_webhook_url": info.get("source_webhook_url"),
            "target_channel_id": info.get("target_id"),
            "target_channel_name": info.get("target_name", ""),
            "target_webhook_url": info.get("target_webhook_url"),
            "channel_type": info.get("type", ""),
            "error": info.get("error"),
        })
    return json.dumps(export_data, indent=indent, ensure_ascii=False)


def export_csv(mapping: dict[str, dict]) -> str:
    """Export mapping as CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "source_channel_id", "source_channel_name", "source_webhook_url",
        "target_channel_id", "target_channel_name", "target_webhook_url",
        "channel_type", "error",
    ])
    for source_id, info in mapping.items():
        writer.writerow([
            source_id,
            info.get("source_name", ""),
            info.get("source_webhook_url", ""),
            info.get("target_id", ""),
            info.get("target_name", ""),
            info.get("target_webhook_url", ""),
            info.get("type", ""),
            info.get("error", ""),
        ])
    return output.getvalue()


def export_markdown(mapping: dict[str, dict]) -> str:
    """Export mapping as Markdown table."""
    lines = [
        "| Source Channel | Source Webhook | Target Channel | Target Webhook | Type | Status |",
        "|---|---|---|---|---|---|",
    ]
    for source_id, info in mapping.items():
        status = "OK" if not info.get("error") else f"ERROR: {info['error']}"
        src_name = info.get("source_name", "N/A")
        src_wh = (info.get("source_webhook_url") or "N/A")[:50]
        tgt_name = info.get("target_name") or "FAILED"
        tgt_wh = (info.get("target_webhook_url") or "N/A")[:50]
        ch_type = info.get("type", "?")
        lines.append(
            f"| {src_name} | {src_wh} | {tgt_name} | {tgt_wh} | {ch_type} | {status} |"
        )
    return "\n".join(lines)


def export_mapping(mapping: dict[str, dict], fmt: str = "json") -> str:
    """Export mapping in requested format."""
    if fmt == "csv":
        return export_csv(mapping)
    elif fmt == "markdown":
        return export_markdown(mapping)
    else:
        return export_json(mapping)
