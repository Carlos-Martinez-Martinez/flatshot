"""
Queue Worker for FlatShot
Manages a queue of folders for batch processing.
"""
from pathlib import Path
from typing import List
from time import time
from PyQt6.QtCore import QThread, pyqtSignal
from flatshot.core.models import ShadowSettings, ExportConfig, CurveData, JobItem
from flatshot.workers.export_worker import ExportWorker
from flatshot.utils.log_manager import LogManager


class QueueWorker(QThread):
    """Worker thread that processes a queue of folder jobs sequentially."""
    
    # Signals for queue status
    queue_started = pyqtSignal(int)  # total_jobs
    job_started = pyqtSignal(int, str)  # job_index, folder_path
    job_progress = pyqtSignal(int, int)  # job_index, progress_percent
    job_completed = pyqtSignal(int, bool, int, int, float)  # index, success, processed, total, duration
    queue_finished = pyqtSignal(int, int, int)  # completed_jobs, errors, total_images
    log_message = pyqtSignal(str)  # log messages
    
    def __init__(self, jobs: List[JobItem], shadow_settings: ShadowSettings,
                 export_config: ExportConfig, curve_data: CurveData,
                 preset_name: str = None):
        super().__init__()
        self.jobs = jobs
        self.settings = shadow_settings
        self.export_config = export_config
        self.curve_data = curve_data
        self.preset_name = preset_name
        self.is_running = True
        self.is_paused = False
        self.current_worker = None
        self.logger = LogManager.get_instance()
    
    def run(self):
        """Process all jobs in the queue."""
        total_jobs = len(self.jobs)
        if total_jobs == 0:
            self.queue_finished.emit(0, 0, 0)
            return
        
        self.logger.log_queue_start(total_jobs)
        self.queue_started.emit(total_jobs)
        
        completed = 0
        errors = 0
        total_images = 0
        
        for index, job in enumerate(self.jobs):
            if not self.is_running:
                # Mark remaining jobs as cancelled
                job.status = "cancelled"
                continue
            
            # Wait if paused
            while self.is_paused and self.is_running:
                self.msleep(100)
            
            if not self.is_running:
                job.status = "cancelled"
                continue
            
            # Process this job
            job.status = "processing"
            folder_path = Path(job.folder_path)
            
            # Count images (use snapshot list if available)
            if job.input_files:
                images = [Path(p) for p in job.input_files if Path(p).suffix.lower() == ".png"]
            else:
                images = list(folder_path.glob("*.png"))
            job.total_images = len(images)
            
            self.job_started.emit(index, str(folder_path))
            self.logger.log_export_start(folder_path.name, job.total_images, self.preset_name)
            
            if job.total_images == 0:
                job.status = "completed"
                job.progress = 100
                self.job_completed.emit(index, True, 0, 0, 0.0)
                completed += 1
                continue
            
            # Create worker for this job
            start_time = time()
            self.current_worker = ExportWorker(
                str(folder_path),
                self.settings,
                self.export_config,
                self.curve_data,
                self.preset_name,
                input_files=[str(p) for p in images] if images else None
            )
            
            # Connect signals
            processed_ok = [0]   # Use list to allow modification in closure
            processed_err = [0]
            
            def on_progress(p):
                job.progress = p
                self.job_progress.emit(index, p)
            
            def on_image_completed(name, success):
                if success:
                    processed_ok[0] += 1
                else:
                    processed_err[0] += 1
                job.processed_images = processed_ok[0]
            
            def on_error(msg):
                self.log_message.emit(msg)
            
            self.current_worker.progress_updated.connect(on_progress)
            self.current_worker.image_completed.connect(on_image_completed)
            self.current_worker.log_updated.connect(on_error)
            
            # Run synchronously within this thread
            self.current_worker.run()
            
            duration = time() - start_time
            
            if not self.is_running:
                job.status = "cancelled"
                self.logger.log_export_cancelled(folder_path.name, processed_ok[0], job.total_images)
            elif processed_err[0] == 0 and processed_ok[0] == job.total_images:
                job.status = "completed"
                completed += 1
                self.logger.log_export_complete(folder_path.name, processed_ok[0], job.total_images, duration)
            else:
                job.status = "error"
                job.error_message = f"Procesadas OK: {processed_ok[0]} / Errores: {processed_err[0]} / Total: {job.total_images}"
                errors += 1
            
            total_images += processed_ok[0]
            self.job_completed.emit(index, job.status == "completed", processed_ok[0], job.total_images, duration)
            
            self.current_worker = None
        
        self.logger.log_queue_complete(completed, errors, total_images)
        self.queue_finished.emit(completed, errors, total_images)
    
    def pause(self):
        """Pause queue progression and current export worker when possible."""
        self.is_paused = True
        if self.current_worker:
            self.current_worker.pause()

    def resume(self):
        """Resume queue progression and current export worker."""
        self.is_paused = False
        if self.current_worker:
            self.current_worker.resume()
    
    def stop(self):
        """Stop the queue and current job."""
        self.is_running = False
        if self.current_worker:
            self.current_worker.stop()
    
    @staticmethod
    def count_images_in_folder(folder_path: str) -> int:
        """Count PNG images in a folder."""
        return len(list(Path(folder_path).glob("*.png")))
