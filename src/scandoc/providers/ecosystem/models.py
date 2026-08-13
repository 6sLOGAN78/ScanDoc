"""
Data models for ProviderDescriptor, ProviderHealth, UserProviderConfig, and FallbackTrace.
"""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from scandoc.agent.taxonomy import Capability
from scandoc.providers.ecosystem.taxonomy import ProviderHealthState, ProviderLifecycleState, ProviderType


class ProviderDescriptor(BaseModel):
    """
    Provider-independent metadata descriptor declaring capabilities, devices, runtimes, and privacy classification.
    """
    provider_id: str = Field(..., description="Stable provider ID (e.g. 'ocr.rapidocr', 'layout.rtdetr')")
    name: str = Field(..., description="Human-readable provider name")
    version: str = Field("1.0.0", description="Provider implementation version")
    capability: Capability = Field(..., description="Primary document processing capability")
    provider_type: ProviderType = Field(ProviderType.LOCAL, description="Execution and hosting model")
    supported_tasks: List[str] = Field(default_factory=list, description="Supported task categories")
    supported_formats: List[str] = Field(default_factory=list, description="Supported file formats")
    supported_devices: List[str] = Field(default_factory=list, description="Supported execution devices")
    supported_runtimes: List[str] = Field(default_factory=list, description="Supported execution runtimes")
    local_or_remote: str = Field("local", description="'local' or 'remote'")
    configuration_schema: Dict[str, Any] = Field(default_factory=dict, description="Configuration options schema")
    model_requirements: Dict[str, Any] = Field(default_factory=dict, description="Required model specs")
    privacy_classification: str = Field("private", description="Privacy rating ('private', 'remote')")
    performance_profile: Dict[str, Any] = Field(default_factory=dict, description="Latency, throughput, and memory hints")


class ProviderHealth(BaseModel):
    """
    Structured health state result for a provider.
    """
    provider_id: str = Field(..., description="Target provider ID")
    state: ProviderHealthState = Field(ProviderHealthState.UNKNOWN, description="Structured health state")
    details: str = Field("", description="Diagnostic details or failure reason")
    checked_at: float = Field(default_factory=time.time, description="Unix timestamp of health check")


class UserProviderConfig(BaseModel):
    """
    User-configurable provider priorities, global overrides, and page-level overrides.
    """
    provider_priority: Dict[Capability, List[str]] = Field(default_factory=dict, description="Priority list of provider IDs per capability")
    overrides: Dict[Capability, str] = Field(default_factory=dict, description="Global capability provider overrides")
    page_overrides: Dict[int, Dict[Capability, str]] = Field(default_factory=dict, description="Page-specific capability overrides")
    options: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Provider-specific configuration settings")


class FallbackTrace(BaseModel):
    """
    Structured trace entry recording provider fallback decisions.
    """
    task: str = Field(..., description="Task or capability category being processed")
    attempt: int = Field(..., ge=1, description="Fallback attempt number")
    provider_id: str = Field(..., description="Evaluated provider ID")
    result: str = Field(..., description="Outcome status ('SELECTED', 'FAILED', 'SKIPPED')")
    reason: str = Field("", description="Reason for selection, failure, or skip")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp")
