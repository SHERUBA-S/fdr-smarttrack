from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class InstitutionBase(BaseModel):
    code: str
    name: str
    state: str
    city: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool = True

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None

class InstitutionResponse(InstitutionBase):
    id: str
    is_synthetic: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BankBase(BaseModel):
    code: str
    name: str
    branch: Optional[str] = None
    ifsc_prefix: Optional[str] = None
    is_active: bool = True

class BankCreate(BankBase):
    pass

class BankResponse(BankBase):
    id: str
    is_synthetic: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
