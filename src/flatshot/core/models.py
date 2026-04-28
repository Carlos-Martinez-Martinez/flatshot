from pydantic import BaseModel, Field
from typing import Tuple, List, Optional, Dict

class ShadowSettings(BaseModel):
    angle: int = Field(180, ge=0, le=360)
    distance: int = 25
    blur: int = 30
    spread: int = 0
    fusion: int = 1
    opacity: int = 20
    noise: int = 2
    padding: int = 10
    contact_blur: int = 10
    contraction: int = 0
    adaptive_zoom: bool = True
    transparent_bg: bool = False
    bg_color: Tuple[int, int, int] = (230, 230, 230)

class ExportConfig(BaseModel):
    output_folder_name: str = "_SALIDA_PRO"
    suffix: str = "_PRO"
    format: str = "JPG"
    transparent_bg: bool = False
    bg_color: Tuple[int, int, int] = (230, 230, 230)
    # New fields for configurable output size
    output_width: int = 1800
    output_height: int = 2400
    # Naming template: {original}, {suffix}, {folder}, {index:03d}
    naming_template: str = "{original}{suffix}"
    # Destination mode: 'subfolder' (create in each source) or 'custom' (single folder)
    output_destination: str = "subfolder"
    custom_output_path: Optional[str] = None

class CurveData(BaseModel):
    xp: List[float]
    fp: List[float]
    base_fill: float = Field(0.52, ge=0.10, le=0.90)
    aspect_mix: float = Field(0.45, ge=0.0, le=1.0)
    occupancy_influence: float = Field(0.42, ge=0.0, le=1.0)
    manual_curve_strength: float = Field(0.60, ge=0.0, le=1.0)

class JobItem(BaseModel):
    """Represents a folder in the processing queue."""
    folder_path: str
    input_files: Optional[List[str]] = None
    status: str = "pending"  # pending, processing, completed, error, cancelled
    progress: int = 0
    total_images: int = 0
    processed_images: int = 0
    error_message: Optional[str] = None

class PresetCategory(BaseModel):
    """Category containing multiple presets."""
    name: str
    presets: Dict[str, dict] = Field(default_factory=dict)  # preset_name -> ShadowSettings.dict()
    locked: bool = False  # If true, presets cannot be modified

class CategorizedPresets(BaseModel):
    """Root structure for categorized presets."""
    categories: Dict[str, PresetCategory] = Field(default_factory=dict)
    # For backward compatibility, uncategorized presets go here
    uncategorized: Dict[str, dict] = Field(default_factory=dict)
