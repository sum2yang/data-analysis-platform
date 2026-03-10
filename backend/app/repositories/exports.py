from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.export import Export

__all__ = ["ExportRepository"]


class ExportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        run_id: str,
        export_type: str,
        format: str,
        file_path: str,
        status: str = "pending",
    ) -> Export:
        export = Export(
            run_id=run_id,
            export_type=export_type,
            format=format,
            file_path=file_path,
            status=status,
        )
        self.db.add(export)
        self.db.commit()
        self.db.refresh(export)
        return export

    def get_by_id(self, export_id: str) -> Export | None:
        return self.db.query(Export).filter(Export.id == export_id).first()

    def update_status(self, export_id: str, status: str) -> Export | None:
        export = self.get_by_id(export_id)
        if export:
            export.status = status
            self.db.commit()
            self.db.refresh(export)
        return export
