
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import Product, User
from schemas import ProductCreate, ProductUpdate, ProductResponse
from auth import require_admin

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id.desc()).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    name = data.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Product name is required")

    product = Product(
        name=name,
        description=data.description,
        price=data.price,
        stock=data.stock,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    changes = data.model_dump(exclude_unset=True)

    if "name" in changes:
        if changes["name"] is None or not changes["name"].strip():
            raise HTTPException(status_code=400, detail="Invalid product name")
        changes["name"] = changes["name"].strip()

    for field, value in changes.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a product referenced by existing orders",
        )

    return Response(status_code=204)
