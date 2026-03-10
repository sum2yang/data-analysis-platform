from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse

from app.api.deps.auth import get_current_user
from app.core.errors import NotFoundError, ValidationError
from app.db.session import get_db
from app.models.user import User
from app.repositories.datasets import DatasetRepository
from app.schemas.dataset import (
    DatasetColumnResponse,
    DatasetDetailResponse,
    DatasetListItem,
    DatasetPreviewResponse,
    DatasetProfileResponse,
    DatasetRevisionResponse,
    DatasetUploadResponse,
)
from app.services.dataset_ingest_service import DatasetIngestService
from app.services.dataset_profile_service import DatasetProfileService
from app.services.storage_service import StorageService

__all__ = ["router"]

router = APIRouter(prefix="/datasets", tags=["datasets"])

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}


@router.post("/upload", response_model=DatasetUploadResponse)
def upload_dataset(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    if not file.filename:
        raise ValidationError("File name is required")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Unsupported file type: {ext}")

    repo = DatasetRepository(db)
    storage = StorageService()

    name = file.filename.rsplit(".", 1)[0]
    ds = repo.create_dataset(
        owner_id=user.id,
        name=name,
        original_filename=file.filename,
        file_type=ext,
    )

    import uuid
    revision_id = str(uuid.uuid4())

    uploaded_path = storage.save_upload(
        user_id=user.id,
        dataset_id=ds.id,
        revision_id=revision_id,
        file=file,
    )

    df = DatasetIngestService.parse_file(uploaded_path, ext)

    canonical_path = storage.get_canonical_path(
        user_id=user.id,
        dataset_id=ds.id,
        revision_id=revision_id,
    )
    DatasetIngestService.materialize_canonical_csv(df, canonical_path)

    col_defs = DatasetIngestService.infer_columns(df)

    rev = repo.create_revision(
        dataset_id=ds.id,
        version=1,
        storage_path=str(canonical_path),
        row_count=len(df),
        col_count=len(df.columns),
        source_type="upload",
    )
    # Override the auto-generated id with our pre-generated one
    rev.id = revision_id
    db.flush()

    cols = repo.create_columns(revision_id=rev.id, columns=col_defs)
    repo.commit()

    return DatasetUploadResponse(
        id=ds.id,
        name=ds.name,
        revision_id=rev.id,
        row_count=len(df),
        col_count=len(df.columns),
        columns=[DatasetColumnResponse.model_validate(c) for c in cols],
    )


@router.get("", response_model=list[DatasetListItem])
def list_datasets(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    repo = DatasetRepository(db)
    datasets = repo.get_by_owner(user.id)
    return [DatasetListItem.model_validate(d) for d in datasets]


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(
    dataset_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    repo = DatasetRepository(db)
    ds = repo.get_by_id(dataset_id)
    if not ds or ds.owner_id != user.id:
        raise NotFoundError("Dataset not found")
    return DatasetDetailResponse.model_validate(ds)


@router.get("/{dataset_id}/revisions", response_model=list[DatasetRevisionResponse])
def get_revisions(
    dataset_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    repo = DatasetRepository(db)
    ds = repo.get_by_id(dataset_id)
    if not ds or ds.owner_id != user.id:
        raise NotFoundError("Dataset not found")
    return [DatasetRevisionResponse.model_validate(r) for r in ds.revisions]


@router.get("/revisions/{revision_id}/preview", response_model=DatasetPreviewResponse)
def get_preview(
    revision_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    repo = DatasetRepository(db)
    rev = repo.get_revision(revision_id)
    if not rev:
        raise NotFoundError("Revision not found")
    ds = repo.get_by_id(rev.dataset_id)
    if not ds or ds.owner_id != user.id:
        raise NotFoundError("Dataset not found")
    preview = DatasetProfileService.build_preview(Path(rev.storage_path))
    return DatasetPreviewResponse(**preview)


@router.get("/revisions/{revision_id}/profile", response_model=DatasetProfileResponse)
def get_profile(
    revision_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    repo = DatasetRepository(db)
    rev = repo.get_revision(revision_id)
    if not rev:
        raise NotFoundError("Revision not found")
    ds = repo.get_by_id(rev.dataset_id)
    if not ds or ds.owner_id != user.id:
        raise NotFoundError("Dataset not found")
    profile = DatasetProfileService.build_profile(Path(rev.storage_path))
    return DatasetProfileResponse(**profile)


@router.get("/revisions/{revision_id}/download")
def download_revision(
    revision_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    repo = DatasetRepository(db)
    rev = repo.get_revision(revision_id)
    if not rev:
        raise NotFoundError("Revision not found")
    ds = repo.get_by_id(rev.dataset_id)
    if not ds or ds.owner_id != user.id:
        raise NotFoundError("Dataset not found")
    path = Path(rev.storage_path)
    if not path.exists():
        raise NotFoundError("File not found on disk")
    return FileResponse(path, filename=f"{ds.name}_v{rev.version}.csv")
