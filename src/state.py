from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class Demographics(BaseModel):
    name: str = Field(default="[MISSING - CLINICIAN REVIEW REQUIRED]")
    age: str = Field(default="[MISSING - CLINICIAN REVIEW REQUIRED]")
    gender: str = Field(default="[MISSING - CLINICIAN REVIEW REQUIRED]")
    weight: str = Field(default="[MISSING - CLINICIAN REVIEW REQUIRED]")
    sources: List[str] = Field(default_factory=list)

class Diagnoses(BaseModel):
    principal: List[str] = Field(default_factory=list)
    secondary: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

class Medications(BaseModel):
    admission: List[str] = Field(default_factory=list)
    discharge: List[str] = Field(default_factory=list)
    reconciliation_flags: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

class DischargeCondition(BaseModel):
    status: str = Field(default="[MISSING - CLINICIAN REVIEW REQUIRED]")
    vitals: str = Field(default="[MISSING - CLINICIAN REVIEW REQUIRED]")
    sources: List[str] = Field(default_factory=list)

class ClinicianReview(BaseModel):
    safety_concerns: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)

class AgentState(BaseModel):
    """The single source of truth passed through the agent loop."""
    patient_demographics: Demographics = Field(default_factory=Demographics)
    admission_date: str = Field(default="[MISSING - CLINICIAN REVIEW REQUIRED]")
    discharge_date: str = Field(default="[MISSING - CLINICIAN REVIEW REQUIRED]")
    diagnoses: Diagnoses = Field(default_factory=Diagnoses)
    hospital_course: List[str] = Field(default_factory=list)
    procedures: List[str] = Field(default_factory=list)
    medications: Medications = Field(default_factory=Medications)
    allergies: str = Field(default="[MISSING - CLINICIAN REVIEW REQUIRED]")
    follow_up_instructions: str = Field(default="[MISSING - CLINICIAN REVIEW REQUIRED]")
    pending_results: List[str] = Field(default_factory=list)
    discharge_condition: DischargeCondition = Field(default_factory=DischargeCondition)
    clinician_review_required: ClinicianReview = Field(default_factory=ClinicianReview)
    
    # Internal agent control fields (not exported to final JSON)
    iteration_count: int = Field(default=0, exclude=True)
    raw_text: Dict[int, str] = Field(default_factory=dict, exclude=True)
