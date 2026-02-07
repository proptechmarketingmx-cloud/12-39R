"""Rutas de propiedades."""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas import PropertyOut
from app.repository import list_properties, get_property

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("", response_model=List[PropertyOut])
def properties(
	zone: Optional[str] = None,
	price_min: Optional[float] = None,
	price_max: Optional[float] = None,
	tipo: Optional[str] = None,
	bedrooms: Optional[int] = None,
	amenities: Optional[List[str]] = Query(None),
):
	return list_properties(zone=zone, price_min=price_min, price_max=price_max, tipo=tipo, bedrooms=bedrooms, amenities=amenities)


@router.get("/{prop_id}", response_model=PropertyOut)
def property_by_id(prop_id: int):
	item = get_property(prop_id)
	if not item:
		raise HTTPException(status_code=404, detail="Propiedad no encontrada")
	return item
