from dataclasses import dataclass
from typing import Protocol
from pathlib import Path

class UnsupportedCapability(ValueError): pass
class ProviderUnavailable(RuntimeError): pass
class CloudDisabled(PermissionError): pass
class JobCancelled(RuntimeError): pass
class InvalidMediaResult(ValueError): pass

@dataclass(frozen=True)
class MediaRequest:
    task: str
    inputs: dict
    options: dict

@dataclass(frozen=True)
class MediaResult:
    artifacts: list[dict]
    metrics: dict
    provenance: dict

class Provider(Protocol):
    def capabilities(self) -> dict: ...
    def run(self, request: MediaRequest, output_dir: Path) -> MediaResult: ...
