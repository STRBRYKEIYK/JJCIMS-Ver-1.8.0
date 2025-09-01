from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
MYSQL_USER = os.getenv("MYSQL_USER", "jjcims_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "your_password")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "jjcims_db")

# SQLAlchemy setup
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class ItemDB(Base):
    __tablename__ = "ITEMSDB"
    
    ID = Column(Integer, primary_key=True, index=True)
    NAME = Column(String(255), index=True)
    BRAND = Column(String(255))
    TYPE = Column(String(255))
    LOCATION = Column(String(255))
    UNIT_OF_MEASURE = Column(String(50))
    STATUS = Column(String(50))
    BALANCE = Column(Integer)
    IN = Column(Integer)
    OUT = Column(Integer)
    Supplier = Column(String(255))
    PO_no = Column(String(255))

class EmployeeLog(Base):
    __tablename__ = "emp_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    DATE = Column(String(50))
    TIME = Column(String(50))
    NAME = Column(String(255))
    DETAILS = Column(Text)

class AdminLog(Base):
    __tablename__ = "adm_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    DATE = Column(String(50))
    TIME = Column(String(50))
    USER = Column(String(255))
    DETAILS = Column(Text)

class EmployeeList(Base):
    __tablename__ = "emp_list"
    
    id = Column(Integer, primary_key=True, index=True)
    Username = Column(String(255), unique=True)
    Password = Column(String(255))
    Access_Level = Column(Integer)
    TFA_Secret = Column(String(255))

# Pydantic models for API
class ItemBase(BaseModel):
    NAME: str
    BRAND: Optional[str] = None
    TYPE: Optional[str] = None
    LOCATION: Optional[str] = None
    UNIT_OF_MEASURE: Optional[str] = None
    STATUS: Optional[str] = None
    BALANCE: Optional[int] = 0
    IN: Optional[int] = 0
    OUT: Optional[int] = 0
    Supplier: Optional[str] = None
    PO_no: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    ID: int
    
    class Config:
        orm_mode = True

class EmployeeLogBase(BaseModel):
    DATE: str
    TIME: str
    NAME: str
    DETAILS: str

class EmployeeLogCreate(EmployeeLogBase):
    pass

class EmployeeLogOut(EmployeeLogBase):
    id: int
    
    class Config:
        orm_mode = True

class AdminLogBase(BaseModel):
    DATE: str
    TIME: str
    USER: str
    DETAILS: str

class AdminLogCreate(AdminLogBase):
    pass

class AdminLogOut(AdminLogBase):
    id: int
    
    class Config:
        orm_mode = True

class EmployeeBase(BaseModel):
    Username: str
    Password: str
    Access_Level: int
    TFA_Secret: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int
    
    class Config:
        orm_mode = True

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create FastAPI app
app = FastAPI(title="JJCIMS API")

# Configure CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoints for Items
@app.get("/items/", response_model=List[Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(ItemDB).offset(skip).limit(limit).all()
    return items

@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ItemDB).filter(ItemDB.ID == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.post("/items/", response_model=Item)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = ItemDB(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: ItemBase, db: Session = Depends(get_db)):
    db_item = db.query(ItemDB).filter(ItemDB.ID == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(ItemDB).filter(ItemDB.ID == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    return {"detail": "Item deleted successfully"}

# API endpoints for Employee Logs
@app.get("/employee-logs/", response_model=List[EmployeeLogOut])
def read_employee_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(EmployeeLog).order_by(EmployeeLog.DATE.desc(), EmployeeLog.TIME.desc()).offset(skip).limit(limit).all()
    return logs

@app.post("/employee-logs/", response_model=EmployeeLogOut)
def create_employee_log(log: EmployeeLogCreate, db: Session = Depends(get_db)):
    db_log = EmployeeLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@app.delete("/employee-logs/")
def clear_employee_logs(db: Session = Depends(get_db)):
    db.query(EmployeeLog).delete()
    db.commit()
    return {"detail": "Employee logs cleared"}

# API endpoints for Admin Logs
@app.get("/admin-logs/", response_model=List[AdminLogOut])
def read_admin_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(AdminLog).order_by(AdminLog.DATE.desc(), AdminLog.TIME.desc()).offset(skip).limit(limit).all()
    return logs

@app.post("/admin-logs/", response_model=AdminLogOut)
def create_admin_log(log: AdminLogCreate, db: Session = Depends(get_db)):
    db_log = AdminLog(**log.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@app.delete("/admin-logs/")
def clear_admin_logs(db: Session = Depends(get_db)):
    db.query(AdminLog).delete()
    db.commit()
    return {"detail": "Admin logs cleared"}

# API endpoints for Employees
@app.get("/employees/", response_model=List[Employee])
def read_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    employees = db.query(EmployeeList).offset(skip).limit(limit).all()
    return employees

@app.get("/employees/{username}", response_model=Employee)
def read_employee(username: str, db: Session = Depends(get_db)):
    employee = db.query(EmployeeList).filter(EmployeeList.Username == username).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@app.post("/employees/", response_model=Employee)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = EmployeeList(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

@app.put("/employees/{username}", response_model=Employee)
def update_employee(username: str, employee: EmployeeBase, db: Session = Depends(get_db)):
    db_employee = db.query(EmployeeList).filter(EmployeeList.Username == username).first()
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    for key, value in employee.dict().items():
        setattr(db_employee, key, value)
    
    db.commit()
    db.refresh(db_employee)
    return db_employee

# Custom query endpoints (recreating original queries.py functionality)
@app.put("/items/{name}/out/{qty}")
def update_item_out(name: str, qty: int, db: Session = Depends(get_db)):
    """Increment the OUT counter for an item by name."""
    db_item = db.query(ItemDB).filter(ItemDB.NAME == name).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db_item.OUT += qty
    db.commit()
    return {"detail": f"Updated OUT quantity for {name} by {qty}"}

@app.get("/items/{name}/unit-of-measure")
def get_unit_of_measure(name: str, db: Session = Depends(get_db)):
    """Return the unit of measure string for an item name."""
    db_item = db.query(ItemDB).filter(ItemDB.NAME == name).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"unit_of_measure": db_item.UNIT_OF_MEASURE}

@app.get("/items/employee-dashboard")
def fetch_items_for_employee_dashboard(db: Session = Depends(get_db)):
    """Return rows for the employee dashboard item list."""
    items = db.query(ItemDB.ID, ItemDB.NAME, ItemDB.Supplier, ItemDB.PO_no).all()
    return items

@app.get("/items/by-type/{category}")
def fetch_items_by_type(category: str, db: Session = Depends(get_db)):
    """Return item rows filtered by TYPE."""
    items = db.query(ItemDB).filter(ItemDB.TYPE == category).all()
    return items

@app.get("/employees/{username_lower}/2fa-and-access")
def get_emp_2fa_and_access(username_lower: str, db: Session = Depends(get_db)):
    """Return 2FA Secret and Access Level for a lowercase username."""
    db_employee = db.query(EmployeeList).filter(func.lower(EmployeeList.Username) == username_lower).first()
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {"2fa_secret": db_employee.TFA_Secret, "access_level": db_employee.Access_Level}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
