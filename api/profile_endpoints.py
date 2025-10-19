"""
ATS MAFIA Framework Profiles API Endpoints

This module implements a minimal CRUD API for Profiles to support the SPA via ATSAPIClient.
It provides a FastAPI router under the base path: /api/v1/profiles and uses a simple
file-backed storage under the 'profiles/' directory.

Notes:
- This module does NOT mount the router; integration is a separate task.
- Storage is independent and thread-safe with atomic writes.
- Existing complex profile JSONs (with "metadata") are normalized for UI compatibility.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Constants and utilities
# -----------------------------------------------------------------------------

ALLOWED_TYPES = {"red_team", "blue_team", "social_engineer"}
ALLOWED_SKILL_LEVELS = {"beginner", "intermediate", "advanced", "expert"}
ALLOWED_STATUS = {"active", "inactive", "training"}


def utc_now_iso() -> str:
    """Return current UTC time in ISO 8601 with trailing Z and no microseconds."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        return int(val)
    except Exception:
        return default


# -----------------------------------------------------------------------------
# Pydantic models
# -----------------------------------------------------------------------------

class ProfileBase(BaseModel):
    """Base fields shared across profile models."""
    name: str = Field(..., description="Human-friendly profile name")
    type: str = Field(..., description=f"Profile type. One of: {sorted(ALLOWED_TYPES)}")
    description: Optional[str] = Field("", description="Optional description")
    skill_level: str = Field(
        "beginner",
        description=f"Skill level. One of: {sorted(ALLOWED_SKILL_LEVELS)}",
    )
    specialization: Optional[str] = Field("", description="Optional specialization")
    avatar: Optional[str] = Field(None, description="Optional avatar URL")
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary configuration dict"
    )

    @validator("type")
    def validate_type(cls, v: str) -> str:
        if v not in ALLOWED_TYPES:
            raise ValueError(f"Invalid type '{v}'. Allowed: {sorted(ALLOWED_TYPES)}")
        return v

    @validator("skill_level")
    def validate_skill_level(cls, v: str) -> str:
        if v not in ALLOWED_SKILL_LEVELS:
            raise ValueError(
                f"Invalid skill_level '{v}'. Allowed: {sorted(ALLOWED_SKILL_LEVELS)}"
            )
        return v

    @validator("configuration")
    def validate_configuration(cls, v: Any) -> Dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError("configuration must be an object/dict")
        return v


class ProfileCreate(ProfileBase):
    """Request model for creating a profile."""
    pass


class ProfileUpdate(BaseModel):
    """Request model for updating a profile. All fields optional."""
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    skill_level: Optional[str] = None
    specialization: Optional[str] = None
    avatar: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    status: Optional[str] = None  # allow direct status update via PUT too

    @validator("type")
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_TYPES:
            raise ValueError(f"Invalid type '{v}'. Allowed: {sorted(ALLOWED_TYPES)}")
        return v

    @validator("skill_level")
    def validate_skill_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_SKILL_LEVELS:
            raise ValueError(
                f"Invalid skill_level '{v}'. Allowed: {sorted(ALLOWED_SKILL_LEVELS)}"
            )
        return v

    @validator("status")
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_STATUS:
            raise ValueError(f"Invalid status '{v}'. Allowed: {sorted(ALLOWED_STATUS)}")
        return v

    @validator("configuration")
    def validate_configuration(cls, v: Optional[Any]) -> Optional[Dict[str, Any]]:
        if v is not None and not isinstance(v, dict):
            raise ValueError("configuration must be an object/dict")
        return v


class ProfileOut(BaseModel):
    """Response model for a stored profile."""
    id: str
    name: str
    type: str
    description: Optional[str] = ""
    skill_level: str
    specialization: Optional[str] = ""
    status: str
    avatar: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ValidationResponse(BaseModel):
    """Response model for validation endpoint."""
    valid: bool
    errors: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Storage
# -----------------------------------------------------------------------------

class FileProfileStorage:
    """
    Minimal file-backed storage for profiles.

    - Directory: profiles/
    - Filename: profiles/{id}.json
    - Schema persisted matches ProfileOut; existing complex profiles will be normalized.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    # ---------- helpers ----------

    def _path_for(self, profile_id: str) -> Path:
        return self.base_dir / f"{profile_id}.json"

    def _atomic_write(self, path: Path, content: Dict[str, Any]) -> None:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)
        os.replace(temp_path, path)

    def _normalize_loaded(self, data: Dict[str, Any], fallback_filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Normalize arbitrary JSON to ProfileOut-compatible dict.

        Supports:
        - Canonical schema (already matches)
        - Complex schema with top-level "metadata"
        Returns normalized dict or None if cannot normalize.
        """
        # Canonical
        if all(k in data for k in ("id", "name", "type", "skill_level", "status", "created_at", "updated_at", "configuration")):
            return {
                "id": str(data["id"]),
                "name": data.get("name", ""),
                "type": data.get("type", ""),
                "description": data.get("description", ""),
                "skill_level": data.get("skill_level", "beginner"),
                "specialization": data.get("specialization", ""),
                "status": data.get("status", "inactive"),
                "avatar": data.get("avatar"),
                "configuration": data.get("configuration", {}) if isinstance(data.get("configuration", {}), dict) else {},
                "created_at": data.get("created_at") or utc_now_iso(),
                "updated_at": data.get("updated_at") or utc_now_iso(),
            }

        # Complex schema with metadata
        meta = data.get("metadata")
        if isinstance(meta, dict) and "id" in meta and "name" in meta and "profile_type" in meta:
            # Map skill_level heuristically from capabilities if present
            cap_levels = set()
            for cap in data.get("capabilities", []) or []:
                lvl = (cap or {}).get("skill_level")
                if isinstance(lvl, str):
                    cap_levels.add(lvl.lower())
            # Map to allowed range
            if "master" in cap_levels or "expert" in cap_levels:
                skill_level = "expert"
            elif "advanced" in cap_levels:
                skill_level = "advanced"
            elif "intermediate" in cap_levels:
                skill_level = "intermediate"
            else:
                skill_level = "beginner"

            created_at = meta.get("created_at") or utc_now_iso()
            updated_at = meta.get("updated_at") or created_at

            # Only accept allowed profile types; otherwise skip normalization
            ptype = str(meta.get("profile_type", "")).lower()
            if ptype not in ALLOWED_TYPES:
                # If not an allowed type, try to coerce from known synonyms or skip
                # For now, skip to avoid confusing UI filters
                logger.debug(f"Skipping profile with unsupported type '{ptype}' from file '{fallback_filename}'")
                return None

            return {
                "id": str(meta.get("id")),
                "name": meta.get("name", ""),
                "type": ptype,
                "description": meta.get("description", ""),
                "skill_level": skill_level,
                "specialization": meta.get("category", "") or "",
                "status": "inactive",
                "avatar": None,
                "configuration": data.get("configuration", {}) if isinstance(data.get("configuration", {}), dict) else data.get("llm_configuration", {}) if isinstance(data.get("llm_configuration", {}), dict) else {},
                "created_at": created_at,
                "updated_at": updated_at,
            }

        # Unable to normalize
        return None

    def _load_one(self, path: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return self._normalize_loaded(raw, fallback_filename=str(path.name))
        except Exception as e:
            logger.warning(f"Failed to read/normalize profile file '{path}': {e}")
            return None

    # ---------- public API ----------

    def list_profiles(self) -> List[Dict[str, Any]]:
        with self.lock:
            results: List[Dict[str, Any]] = []
            for p in sorted(self.base_dir.glob("*.json")):
                prof = self._load_one(p)
                if prof:
                    results.append(prof)
            return results

    def get_profile(self, profile_id: str) -> Dict[str, Any]:
        with self.lock:
            path = self._path_for(profile_id)
            if path.exists():
                prof = self._load_one(path)
                if prof:
                    return prof
            # As a fallback, scan directory in case file uses non-canonical schema name
            for p in self.base_dir.glob("*.json"):
                prof = self._load_one(p)
                if prof and prof.get("id") == profile_id:
                    return prof
            raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")

    def create_profile(self, payload: ProfileCreate) -> Dict[str, Any]:
        with self.lock:
            new_id = str(uuid.uuid4())
            now = utc_now_iso()
            doc = {
                "id": new_id,
                "name": payload.name,
                "type": payload.type,
                "description": payload.description or "",
                "skill_level": payload.skill_level,
                "specialization": payload.specialization or "",
                "status": "inactive",
                "avatar": payload.avatar,
                "configuration": payload.configuration or {},
                "created_at": now,
                "updated_at": now,
            }
            path = self._path_for(new_id)
            self._atomic_write(path, doc)
            return doc

    def update_profile(self, profile_id: str, payload: ProfileUpdate) -> Dict[str, Any]:
        with self.lock:
            current = self.get_profile(profile_id)
            updated = dict(current)
            # Apply updates if provided
            for field in ("name", "type", "description", "skill_level", "specialization", "avatar", "status"):
                val = getattr(payload, field)
                if val is not None:
                    updated[field] = val
            if payload.configuration is not None:
                updated["configuration"] = payload.configuration
            updated["updated_at"] = utc_now_iso()
            path = self._path_for(profile_id)
            self._atomic_write(path, updated)
            return updated

    def delete_profile(self, profile_id: str) -> Dict[str, Any]:
        with self.lock:
            path = self._path_for(profile_id)
            if path.exists():
                try:
                    os.remove(path)
                    return {"id": profile_id, "deleted": True}
                except Exception as e:
                    logger.error(f"Failed to delete profile '{profile_id}': {e}")
                    raise HTTPException(status_code=500, detail="Failed to delete profile")
            # If not found, still confirm existence by scanning normalized profiles
            for p in self.base_dir.glob("*.json"):
                prof = self._load_one(p)
                if prof and prof.get("id") == profile_id:
                    try:
                        os.remove(p)
                        return {"id": profile_id, "deleted": True}
                    except Exception as e:
                        logger.error(f"Failed to delete profile '{profile_id}': {e}")
                        raise HTTPException(status_code=500, detail="Failed to delete profile")
            raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")

    def set_status(self, profile_id: str, status: str) -> Dict[str, Any]:
        if status not in ALLOWED_STATUS:
            raise HTTPException(status_code=400, detail=f"Invalid status '{status}'")
        with self.lock:
            current = self.get_profile(profile_id)
            current["status"] = status
            current["updated_at"] = utc_now_iso()
            path = self._path_for(profile_id)
            self._atomic_write(path, current)
            return current

    def validate_payload(self, data: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        # Required fields
        for req in ("name", "type"):
            if not data.get(req):
                errors.append(f"Missing required field: {req}")
        # Enumerations
        t = data.get("type")
        if t is not None and t not in ALLOWED_TYPES:
            errors.append(f"Invalid type '{t}'. Allowed: {sorted(ALLOWED_TYPES)}")
        sl = data.get("skill_level", "beginner")
        if sl not in ALLOWED_SKILL_LEVELS:
            errors.append(f"Invalid skill_level '{sl}'. Allowed: {sorted(ALLOWED_SKILL_LEVELS)}")
        # Configuration must be dict if provided
        cfg = data.get("configuration", {})
        if not isinstance(cfg, dict):
            errors.append("configuration must be an object/dict")
        return errors

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = (query or "").strip().lower()
        if not q:
            return []
        results: List[Dict[str, Any]] = []
        for prof in self.list_profiles():
            haystacks = [
                (prof.get("name") or "").lower(),
                (prof.get("description") or "").lower(),
                (prof.get("specialization") or "").lower(),
            ]
            if any(q in h for h in haystacks):
                results.append(prof)
        return results


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])
_storage = FileProfileStorage(Path("profiles"))


@router.get("/", response_model=List[ProfileOut])
async def list_profiles():
    """
    List profiles.

    Returns:
        List[ProfileOut]: All known profiles, normalized for UI consumption.
    """
    try:
        return _storage.list_profiles()
    except Exception as e:
        logger.error(f"Error listing profiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to list profiles")


@router.get("/search", response_model=List[ProfileOut])
async def search_profiles(q: str = Query(..., min_length=1, description="Query string")):
    """
    Search profiles by case-insensitive substring across name, description, and specialization.

    Parameters:
        q (str): Query string.

    Returns:
        List[ProfileOut]: Matching profiles.
    """
    try:
        return _storage.search(q)
    except Exception as e:
        logger.error(f"Error searching profiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to search profiles")


@router.post("/validate", response_model=ValidationResponse)
async def validate_profile(payload: Dict[str, Any]):
    """
    Validate a profile payload (without creating it).

    Checks:
    - Required fields: name, type
    - Enumerations: type, skill_level
    - configuration must be a dict

    Returns:
        ValidationResponse: { valid: bool, errors: [...] }
    """
    try:
        errors = _storage.validate_payload(payload or {})
        return ValidationResponse(valid=len(errors) == 0, errors=errors)
    except Exception as e:
        logger.error(f"Error validating profile: {e}")
        raise HTTPException(status_code=400, detail=f"Validation failed: {e}")


@router.get("/{profile_id}", response_model=ProfileOut)
async def get_profile(profile_id: str):
    """
    Get a profile by ID.

    Parameters:
        profile_id (str): Profile identifier.

    Returns:
        ProfileOut: The requested profile, if found.
    """
    try:
        return _storage.get_profile(profile_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile '{profile_id}': {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")


@router.post("/", response_model=ProfileOut, status_code=201)
async def create_profile(payload: ProfileCreate):
    """
    Create a new profile.

    Body:
        ProfileCreate: { name, type, description?, skill_level?, specialization?, avatar?, configuration? }

    Behavior:
        - Generates id (UUID4)
        - status defaults to 'inactive'
        - created_at and updated_at set to now

    Returns:
        ProfileOut: The created profile.
    """
    try:
        return _storage.create_profile(payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to create profile")


@router.put("/{profile_id}", response_model=ProfileOut)
async def update_profile(profile_id: str, payload: ProfileUpdate):
    """
    Update a profile.

    Parameters:
        profile_id (str): Profile identifier.

    Body:
        ProfileUpdate: Partial fields to update.

    Returns:
        ProfileOut: The updated profile.

    Errors:
        404 if profile not found.
        400 for invalid field values.
    """
    try:
        return _storage.update_profile(profile_id, payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile '{profile_id}': {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str):
    """
    Delete a profile.

    Parameters:
        profile_id (str): Profile identifier.

    Returns:
        dict: { id: str, deleted: bool }

    Errors:
        404 if profile not found.
    """
    try:
        return _storage.delete_profile(profile_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting profile '{profile_id}': {e}")
        raise HTTPException(status_code=500, detail="Failed to delete profile")


@router.post("/{profile_id}/activate", response_model=ProfileOut)
async def activate_profile(profile_id: str):
    """
    Activate a profile (set status='active').

    Parameters:
        profile_id (str): Profile identifier.

    Returns:
        ProfileOut: The updated profile.
    """
    try:
        return _storage.set_status(profile_id, "active")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating profile '{profile_id}': {e}")
        raise HTTPException(status_code=500, detail="Failed to activate profile")


@router.post("/{profile_id}/deactivate", response_model=ProfileOut)
async def deactivate_profile(profile_id: str):
    """
    Deactivate a profile (set status='inactive').

    Parameters:
        profile_id (str): Profile identifier.

    Returns:
        ProfileOut: The updated profile.
    """
    try:
        return _storage.set_status(profile_id, "inactive")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating profile '{profile_id}': {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate profile")


# Export router
__all__ = ["router"]