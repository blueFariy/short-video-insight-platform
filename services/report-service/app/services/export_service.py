"""
Export Service - Export reports to various formats
"""
import io
import csv
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from pathlib import Path


class ExportService:
    """Export service for generating files"""

    def __init__(self):
        self.export_dir = Path("./exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def export_to_json(
        self,
        data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export data to JSON"""
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        file_path = self.export_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported to JSON: {file_path}")
        return {
            "filename": filename,
            "file_path": str(file_path),
            "size": file_path.stat().st_size
        }

    async def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export data to CSV"""
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        if not data:
            raise ValueError("No data to export")

        file_path = self.export_dir / filename

        # Get all keys from first record
        fieldnames = list(data[0].keys())

        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Exported to CSV: {file_path}")
        return {
            "filename": filename,
            "file_path": str(file_path),
            "size": file_path.stat().st_size,
            "rows": len(data)
        }

    async def export_to_excel(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export data to Excel (simplified CSV with .xlsx extension)"""
        # For simplicity, we'll create a CSV that can be opened in Excel
        # In production, use openpyxl
        if not filename:
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # Use CSV export for now (Excel can open CSV)
        csv_result = await self.export_to_csv(data, filename.replace(".xlsx", ".csv"))

        return {
            "filename": filename,
            "file_path": csv_result["file_path"],
            "size": csv_result["size"],
            "rows": csv_result["rows"],
            "note": "Exported as CSV (compatible with Excel)"
        }

    async def export_report(
        self,
        report_data: Dict[str, Any],
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export report in specified format"""
        if format == "json":
            return await self.export_to_json(report_data)
        elif format == "csv":
            # Flatten data for CSV
            if "videos" in report_data:
                return await self.export_to_csv(report_data["videos"])
            elif "accounts" in report_data:
                return await self.export_to_csv(report_data["accounts"])
            elif "trend_data" in report_data:
                return await self.export_to_csv(report_data["trend_data"])
            else:
                # Convert single record to list
                return await self.export_to_csv([report_data])
        elif format == "excel":
            return await self.export_to_excel(report_data.get("videos", [report_data]))
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_export_formats(self) -> List[str]:
        """Get supported export formats"""
        return ["json", "csv", "excel"]


export_service = ExportService()
