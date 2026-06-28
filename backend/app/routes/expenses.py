from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Expense
from app.schemas import ExpenseCreate, ExpenseListResponse, ExpenseRead, ExpenseUpdate
from app.services.jwt_auth import get_current_user

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("/", response_model=ExpenseRead)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
):
    db_expense = Expense(**expense.model_dump())
    db_expense.user_id = current_user_id
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.get("/", response_model=ExpenseListResponse)
def list_expenses(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
    merchant: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(Expense).filter(Expense.user_id == current_user_id)
    if merchant:
        query = query.filter(Expense.merchant.ilike(f"%{merchant}%"))
    if category:
        query = query.filter(Expense.category.ilike(f"%{category}%"))
    if type:
        query = query.filter(Expense.type == type)

    total = query.count()
    expenses = (
        query.order_by(Expense.date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"items": expenses, "total": total}


@router.get("/{expense_id}", response_model=ExpenseRead)
def get_expense(expense_id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user_id).first()
    if not exp:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Expense not found")
    return exp


@router.put("/{expense_id}", response_model=ExpenseRead)
def update_expense(expense_id: int, payload: "ExpenseUpdate", db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    from fastapi import HTTPException
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(exp, k, v)
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    from fastapi import HTTPException
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(exp)
    db.commit()
    return {"deleted": True}



@router.patch("/{expense_id}", response_model=ExpenseRead)
def patch_expense(expense_id: int, payload: "ExpenseUpdate", db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    from fastapi import HTTPException
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(exp, k, v)
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp
