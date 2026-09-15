import os
import shutil
import uuid
import re
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")


def process_generated_chart(source_path: str = "outputs/chart.png") -> Optional[str]:
    """
    If source_path exists, copy it to a unique file outputs/chart_<uuid>.png
    and return the relative API path /api/charts/chart_<uuid>.png.
    """
    abs_source = os.path.join(BASE_DIR, source_path) if not os.path.isabs(source_path) else source_path
    
    if not os.path.exists(abs_source):
        return None

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    unique_id = f"chart_{uuid.uuid4().hex}"
    filename = f"{unique_id}.png"
    target_path = os.path.join(OUTPUTS_DIR, filename)

    shutil.copy2(abs_source, target_path)

    return f"/api/charts/{filename}"


def get_safe_chart_path(chart_id: str) -> Optional[str]:
    """
    Safely resolve a chart file path under outputs/ directory preventing directory traversal.
    """
    # Sanitize chart_id: allow only alphanumeric, underscores, hyphens, dots
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", chart_id):
        return None

    filename = chart_id if chart_id.endswith(".png") else f"{chart_id}.png"
    target_path = os.path.abspath(os.path.join(OUTPUTS_DIR, filename))

    # Verify the target path is strictly within OUTPUTS_DIR
    real_outputs_dir = os.path.realpath(OUTPUTS_DIR)
    real_target_path = os.path.realpath(target_path)

    if not real_target_path.startswith(real_outputs_dir):
        return None

    if os.path.exists(real_target_path) and os.path.isfile(real_target_path):
        return real_target_path

    return None
