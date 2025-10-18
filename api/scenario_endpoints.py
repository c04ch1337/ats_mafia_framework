"""
ATS MAFIA Framework Scenario API Endpoints

REST API endpoints for scenario management including listing, retrieval,
validation, and progress tracking.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File
from pydantic import BaseModel, Field
import json

from ..core.scenario_engine import (
    ScenarioLibrary, ScenarioValidator, Scenario,
    DifficultyLevel, ScenarioType, get_scenario_library
)


# Pydantic models for request/response validation
class ScenarioFilter(BaseModel):
    """Filter parameters for scenario listing."""
    scenario_type: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[List[str]] = None


class ScenarioValidationRequest(BaseModel):
    """Request model for scenario validation."""
    scenario_data: Dict[str, Any] = Field(..., description="Scenario JSON data to validate")


class ScenarioValidationResponse(BaseModel):
    """Response model for scenario validation."""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    scenario_id: Optional[str] = None
    scenario_name: Optional[str] = None


class ScenarioProgressRequest(BaseModel):
    """Request model for updating scenario progress."""
    phase_id: str
    objective_id: str
    status: str
    completed_at: Optional[str] = None


class RecommendationRequest(BaseModel):
    """Request model for scenario recommendations."""
    skill_level: str = Field(..., description="User skill level (novice, intermediate, advanced, expert, master)")
    completed_scenarios: List[str] = Field(default_factory=list, description="List of completed scenario IDs")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of recommendations")


# Create API router
router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


# Initialize scenario library (will be set by application)
_scenario_library: Optional[ScenarioLibrary] = None


def set_scenario_library(library: ScenarioLibrary):
    """Set the global scenario library instance."""
    global _scenario_library
    _scenario_library = library


def get_library() -> ScenarioLibrary:
    """Get scenario library instance."""
    if _scenario_library is None:
        # Try to get global instance
        lib = get_scenario_library()
        if lib is None:
            raise HTTPException(status_code=500, detail="Scenario library not initialized")
        return lib
    return _scenario_library


@router.get("/", response_model=List[Dict[str, Any]])
async def list_scenarios(
    scenario_type: Optional[str] = Query(None, description="Filter by scenario type"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags")
):
    """
    List all available scenarios with optional filtering.
    
    **Parameters:**
    - **scenario_type**: Filter by scenario type (red_team, blue_team, social_engineering, red_vs_blue, multi_stage)
    - **difficulty**: Filter by difficulty (novice, intermediate, advanced, expert, master)
    - **tags**: Filter by tags (scenarios must have at least one matching tag)
    
    **Returns:**
    - List of scenario dictionaries with metadata
    """
    try:
        library = get_library()
        
        # Convert string filters to enums
        type_filter = ScenarioType(scenario_type) if scenario_type else None
        difficulty_filter = DifficultyLevel(difficulty) if difficulty else None
        
        scenarios = library.list_scenarios(
            scenario_type=type_filter,
            difficulty=difficulty_filter,
            tags=tags
        )
        
        return scenarios
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid filter value: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing scenarios: {e}")


@router.get("/{scenario_id}", response_model=Dict[str, Any])
async def get_scenario(scenario_id: str):
    """
    Get detailed information about a specific scenario.
    
    **Parameters:**
    - **scenario_id**: Unique identifier of the scenario
    
    **Returns:**
    - Complete scenario definition including phases, objectives, and scoring
    """
    try:
        library = get_library()
        scenario = library.get_scenario(scenario_id)
        
        if scenario is None:
            raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")
        
        return scenario.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving scenario: {e}")


@router.get("/{scenario_id}/progress", response_model=Dict[str, Any])
async def get_scenario_progress(scenario_id: str, session_id: Optional[str] = Query(None)):
    """
    Get current progress in a scenario.
    
    **Parameters:**
    - **scenario_id**: Unique identifier of the scenario
    - **session_id**: Optional session ID to get progress for specific session
    
    **Returns:**
    - Progress information including completed phases and objectives
    """
    try:
        library = get_library()
        scenario = library.get_scenario(scenario_id)
        
        if scenario is None:
            raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")
        
        # Calculate progress
        total_objectives = scenario.get_total_objectives()
        completed_objectives = scenario.get_completed_objectives()
        completion_percentage = scenario.get_completion_percentage()
        
        progress = {
            'scenario_id': scenario_id,
            'session_id': session_id,
            'total_objectives': total_objectives,
            'completed_objectives': completed_objectives,
            'completion_percentage': completion_percentage,
            'phases': [
                {
                    'phase_id': phase.id,
                    'name': phase.name,
                    'status': phase.status.value,
                    'completion_percentage': phase.get_completion_percentage()
                }
                for phase in scenario.phases
            ]
        }
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving progress: {e}")


@router.post("/validate", response_model=ScenarioValidationResponse)
async def validate_scenario(request: ScenarioValidationRequest):
    """
    Validate a scenario JSON definition.
    
    **Parameters:**
    - **scenario_data**: Complete scenario JSON object to validate
    
    **Returns:**
    - Validation result with any errors found
    """
    try:
        validator = ScenarioValidator()
        
        # Create scenario from data
        scenario = Scenario.from_dict(request.scenario_data)
        
        # Validate
        errors = validator.validate(scenario)
        
        response = ScenarioValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            scenario_id=scenario.id,
            scenario_name=scenario.name
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")


@router.post("/custom", response_model=Dict[str, Any])
async def upload_custom_scenario(
    scenario_file: UploadFile = File(..., description="Scenario JSON file")
):
    """
    Upload and register a custom scenario.
    
    **Parameters:**
    - **scenario_file**: JSON file containing scenario definition
    
    **Returns:**
    - Registration result with scenario ID
    """
    try:
        # Read file content
        content = await scenario_file.read()
        scenario_data = json.loads(content)
        
        # Validate scenario
        validator = ScenarioValidator()
        scenario = Scenario.from_dict(scenario_data)
        errors = validator.validate(scenario)
        
        if errors:
            raise HTTPException(
                status_code=400,
                detail={
                    'message': 'Scenario validation failed',
                    'errors': errors
                }
            )
        
        # Register with library
        library = get_library()
        library.register_scenario(scenario)
        
        return {
            'success': True,
            'scenario_id': scenario.id,
            'scenario_name': scenario.name,
            'message': 'Scenario registered successfully'
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading scenario: {e}")


@router.get("/recommended", response_model=List[Dict[str, Any]])
async def get_recommended_scenarios(
    skill_level: str = Query(..., description="User skill level"),
    completed_scenarios: List[str] = Query(default=[], description="Completed scenario IDs"),
    max_results: int = Query(default=5, ge=1, le=20, description="Maximum recommendations")
):
    """
    Get recommended scenarios based on skill level and progress.
    
    **Parameters:**
    - **skill_level**: User's current skill level (novice, intermediate, advanced, expert, master)
    - **completed_scenarios**: List of scenario IDs the user has completed
    - **max_results**: Maximum number of recommendations to return
    
    **Returns:**
    - List of recommended scenarios tailored to user's skill level
    """
    try:
        library = get_library()
        
        # Convert skill level to enum
        try:
            skill_enum = DifficultyLevel(skill_level)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid skill level. Must be one of: {[d.value for d in DifficultyLevel]}"
            )
        
        # Get recommendations
        recommendations = library.get_recommended_scenarios(
            skill_level=skill_enum,
            completed_scenarios=completed_scenarios,
            max_results=max_results
        )
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {e}")


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_scenarios(
    query: str = Query(..., min_length=1, description="Search query")
):
    """
    Search scenarios by text query.
    
    **Parameters:**
    - **query**: Search query to match against scenario names, descriptions, and tags
    
    **Returns:**
    - List of matching scenarios
    """
    try:
        library = get_library()
        results = library.search_scenarios(query)
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching scenarios: {e}")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_statistics():
    """
    Get statistics about available scenarios.
    
    **Returns:**
    - Statistics including total count, breakdown by type and difficulty
    """
    try:
        library = get_library()
        stats = library.get_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {e}")


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: str):
    """
    Unregister a scenario from the library.
    
    **Parameters:**
    - **scenario_id**: Unique identifier of the scenario to remove
    
    **Returns:**
    - Deletion confirmation
    """
    try:
        library = get_library()
        success = library.unregister_scenario(scenario_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")
        
        return {
            'success': True,
            'scenario_id': scenario_id,
            'message': 'Scenario unregistered successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting scenario: {e}")


# Export router
__all__ = ['router', 'set_scenario_library']