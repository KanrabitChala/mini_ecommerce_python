
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Order, OrderItem, Product, User
from schemas import OrderCreate, OrderResponse
from auth import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Reject duplicate product IDs to keep quantities unambiguous.
    product_ids = [item.product_id for item in data.items]

    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=400,
            detail="Include each product only once per order",
        )

    order = Order(user_id=current_user.id, status="pending")

    try:
        # Lock products in sorted order to reduce concurrent-order conflicts.
        locked_products = {}

        for product_id in sorted(product_ids):
            product = (
                db.query(Product)
                .filter(Product.id == product_id)
                .with_for_update()
                .first()
            )

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {product_id} not found",
                )

            locked_products[product_id] = product

        # Check stock and calculate all prices on the server.
        for requested_item in data.items:
            product = locked_products[requested_item.product_id]

            if product.stock < requested_item.quantity:
                raise HTTPException(
                    status_code=409,
                    detail=f"Insufficient stock for {product.name}",
                )

        db.add(order)
        db.flush()

        for requested_item in data.items:
            product = locked_products[requested_item.product_id]

            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=requested_item.quantity,
                    unit_price=product.price,
                )
            )

            product.stock -= requested_item.quantity

        db.commit()

    except Exception:
        db.rollback()
        raise

    # Reload the order and its items after the transaction commits.
    saved_order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order.id)
        .first()
    )

    return saved_order


@router.get("/my", response_model=list[OrderResponse])
def my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == current_user.id)
        .order_by(Order.id.desc())
        .all()
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
        .first()
    )

    if order is None:
        # Do not reveal another customer's order.
        raise HTTPException(status_code=404, detail="Order not found")

    return order
