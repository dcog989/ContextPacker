from repomix import RepoProcessor, RepomixConfig
from pathlib import Path
import queue
import threading
import logging

from .types import LogMessage, StatusMessage, StatusType


def run_repomix(source_dir, output_filepath, message_queue: queue.Queue, cancel_event: threading.Event, repomix_style="markdown", exclude_patterns=None):
    """
    Runs the repomix packaging process with the specified configuration.

    This function is designed to be run in a separate thread.
    """
    if cancel_event.is_set():
        message_queue.put(StatusMessage(status=StatusType.CANCELLED, message="Skipping packaging because process was cancelled."))
        return

    source_path = Path(source_dir)
    if not source_path.is_dir():
        message_queue.put(StatusMessage(status=StatusType.ERROR, message="ERROR: Source directory for packaging is missing."))
        return

    output_path = Path(output_filepath)
    packaged_filename = output_path.name

    all_excludes = [packaged_filename, Path(output_filepath).name]
    if exclude_patterns:
        all_excludes.extend(exclude_patterns)

    logging.info(f"Running repomix packager on {source_dir}...")
    logging.info(f"Output will be saved to: {output_filepath}")

    try:
        config = RepomixConfig()
        config.output.file_path = str(output_path)
        config.output.style = repomix_style
        config.ignore.custom_patterns = all_excludes
        config.output.calculate_tokens = True
        config.output.show_file_stats = True
        config.security.enable_security_check = False

        processor = RepoProcessor(str(source_path), config=config)

        # Check for cancellation before starting the processor
        if cancel_event.is_set():
            message_queue.put(StatusMessage(status=StatusType.CANCELLED, message="Packaging cancelled by user."))
            return

        result = processor.process()

        # Check for cancellation after processing
        if cancel_event.is_set():
            message_queue.put(StatusMessage(status=StatusType.CANCELLED, message="Packaging cancelled by user."))
            return

        message_queue.put(StatusMessage(status=StatusType.PACKAGE_COMPLETE, message=f"✔ Repomix finished successfully. Output: {result.config.output.file_path}"))

    except Exception as e:
        logging.error(f"An unexpected packaging error occurred: {e}", exc_info=True)
        message_queue.put(StatusMessage(status=StatusType.ERROR, message=f"ERROR: An unexpected packaging error occurred: {e}"))
