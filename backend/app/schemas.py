from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ExpenseBase(BaseModel):
    amount: float
    merchant: str
    category: str
    description: Optional[str] = None
    type: str = "Expense"


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseRead(ExpenseBase):
    id: int
    user_id: Optional[int] = None
    date: datetime

    model_config = ConfigDict(from_attributes=True)


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    merchant: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None


class ExpenseListResponse(BaseModel):
    items: List[ExpenseRead]
    total: int


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
