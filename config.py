from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ETLConfig:
    input_path: Path
    output_dir: Path
    output_format: str
    use_llm: bool = False
