from repomix import RepoProcessor, RepomixConfig
from pathlib import Path


def run_repomix(source_dir, output_filepath, log_queue, cancel_event, repomix_style="markdown", exclude_patterns=None):
    """
    Runs the repomix packaging process with the specified configuration.

    This function is designed to be run in a separate thread.
    """
    if cancel_event.is_set():
        log_queue.put({"type": "status", "status": "cancelled", "message": "Skipping packaging because process was cancelled."})
        return

    source_path = Path(source_dir)
    if not source_path.is_dir():
        log_queue.put({"type": "status", "status": "error", "message": "ERROR: Source directory for packaging is missing."})
        return

    output_path = Path(output_filepath)
    packaged_filename = output_path.name

    all_excludes = [packaged_filename, Path(output_filepath).name]
    if exclude_patterns:
        all_excludes.extend(exclude_patterns)

    log_queue.put({"type": "log", "message": f"Running repomix packager on {source_dir}..."})
    log_queue.put({"type": "log", "message": f"Output will be saved to: {output_filepath}"})

    try:
        config = RepomixConfig()
        config.output.file_path = str(output_path)
        config.output.style = repomix_style
        config.ignore.custom_patterns = all_excludes
        config.output.calculate_tokens = True
        config.output.show_file_stats = True
        config.security.enable_security_check = False

        processor = RepoProcessor(str(source_path), config=config)
        result = processor.process()

        log_queue.put({"type": "status", "status": "package_complete", "message": f"✔ Repomix finished successfully. Output: {result.config.output.file_path}"})

    except Exception as e:
        log_queue.put({"type": "status", "status": "error", "message": f"ERROR: An unexpected packaging error occurred: {e}"})
