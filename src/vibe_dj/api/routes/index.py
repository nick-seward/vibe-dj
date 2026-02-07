import os
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from loguru import logger

from vibe_dj.api.background import JobManager
from vibe_dj.api.dependencies import (
    get_audio_analyzer,
    get_config,
    get_db,
    get_job_manager,
    get_similarity_index,
    parse_config_file,
)
from vibe_dj.api.models import IndexJobResponse, IndexRequest, JobStatusResponse
from vibe_dj.core import AudioAnalyzer, LibraryIndexer, MusicDatabase, SimilarityIndex
from vibe_dj.models import Config

router = APIRouter(prefix="/api", tags=["indexing"])


def run_indexing_job(
    job_id: str,
    library_path: str,
    config: Config,
    job_manager: JobManager,
) -> None:
    """Background task to run library indexing.

    :param job_id: Job identifier for tracking
    :param library_path: Path to music library
    :param config: Configuration object
    :param job_manager: Job manager for status updates
    """
    try:
        job_manager.start_job(job_id)

        if not os.path.exists(library_path):
            raise ValueError(f"Library path does not exist: {library_path}")

        if not os.path.isdir(library_path):
            raise ValueError(f"Library path is not a directory: {library_path}")

        with MusicDatabase(config) as db:
            analyzer = AudioAnalyzer(config)
            similarity_index = SimilarityIndex(config)
            indexer = LibraryIndexer(config, db, analyzer, similarity_index)

            phase_labels = {
                "metadata": "Extracting metadata",
                "features": "Analyzing audio",
            }

            def progress_callback(phase: str, processed: int, total: int) -> None:
                label = phase_labels.get(phase, phase)
                job_manager.update_progress(
                    job_id,
                    {
                        "phase": phase,
                        "processed": processed,
                        "total": total,
                        "message": f"{label} ({processed}/{total})",
                    },
                )

            job_manager.update_progress(
                job_id, {"phase": "scanning", "message": "Scanning music library..."}
            )

            indexer.index_library(library_path, progress_callback=progress_callback)

            job_manager.update_progress(
                job_id,
                {"phase": "completed", "message": "Indexing completed successfully"},
            )

        job_manager.complete_job(job_id)
        logger.info(f"Indexing job {job_id} completed successfully")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Indexing job {job_id} failed: {error_msg}")
        job_manager.fail_job(job_id, error_msg)


@router.post("/index", response_model=IndexJobResponse)
def index_library(
    background_tasks: BackgroundTasks,
    request: IndexRequest,
    config: Config = Depends(get_config),
    job_manager: JobManager = Depends(get_job_manager),
) -> IndexJobResponse:
    """Trigger library indexing as a background task.

    Starts indexing of the specified music library directory. Returns
    immediately with a job ID for status polling.

    :param background_tasks: FastAPI background tasks
    :param request: Index request with library path and config overrides
    :param config: Application configuration
    :param job_manager: Job manager for tracking
    :return: Job response with ID and initial status
    """
    if request.config_overrides:
        config = Config.from_dict({**config.__dict__, **request.config_overrides})

    job_id = job_manager.create_job()

    background_tasks.add_task(
        run_indexing_job,
        job_id,
        request.library_path,
        config,
        job_manager,
    )

    return IndexJobResponse(
        job_id=job_id,
        status="queued",
        message=f"Indexing job queued for {request.library_path}",
    )


@router.post("/index/upload", response_model=IndexJobResponse)
async def index_library_with_config_upload(
    background_tasks: BackgroundTasks,
    library_path: str = Form(...),
    config_file: Optional[UploadFile] = File(None),
    base_config: Config = Depends(get_config),
    job_manager: JobManager = Depends(get_job_manager),
) -> IndexJobResponse:
    """Trigger library indexing with optional config file upload.

    Accepts a config file upload for custom configuration.

    :param background_tasks: FastAPI background tasks
    :param library_path: Path to music library directory
    :param config_file: Optional uploaded config file
    :param base_config: Base application configuration
    :param job_manager: Job manager for tracking
    :return: Job response with ID and initial status
    """
    config = base_config
    if config_file:
        uploaded_config = await parse_config_file(config_file)
        if uploaded_config:
            config = uploaded_config

    job_id = job_manager.create_job()

    background_tasks.add_task(
        run_indexing_job,
        job_id,
        library_path,
        config,
        job_manager,
    )

    return IndexJobResponse(
        job_id=job_id,
        status="queued",
        message=f"Indexing job queued for {library_path}",
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
) -> JobStatusResponse:
    """Get status of an indexing job.

    Poll this endpoint to track progress of a background indexing job.

    :param job_id: Job identifier
    :param job_manager: Job manager for tracking
    :return: Current job status with progress information
    :raises HTTPException: If job not found
    """
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        error=job.error,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )
