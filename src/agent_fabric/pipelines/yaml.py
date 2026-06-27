import yaml
from typing import Union
from pathlib import Path
from agent_fabric.pipelines.dag import Pipeline, validate_dag

__all__ = ["load_pipeline_from_yaml"]


def load_pipeline_from_yaml(path_or_content: Union[str, Path]) -> Pipeline:
    """
    Parses and validates a Pipeline definition from a YAML file path or raw string.
    """
    content = str(path_or_content)
    p = Path(content)
    if p.exists() and p.is_file():
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    else:
        data = yaml.safe_load(content)
        
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML pipeline configuration: {data}")
        
    pipeline = Pipeline(**data)
    validate_dag(pipeline)
    return pipeline
