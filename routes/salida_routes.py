from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas.salida_schema import SalidaCreate, SalidaResponse
from fastapi import HTTPException
from crud import crud_salidas

router = APIRouter(prefix="/salidas", tags=["Salidas"])

@router.post("/")
def crear_salida(data: SalidaCreate, db: Session = Depends(get_db)):
    return crud_salidas.crear_salida(db, data)

@router.get("/{nit}", response_model=list[SalidaResponse])
def listar_salidas_por_nit(nit: str, db: Session = Depends(get_db)):
    salidas = crud_salidas.obtener_salidas_por_nit(db, nit)

    if salidas is None:
        raise HTTPException(status_code=404, detail="El cliente no existe.")

    return salidas
