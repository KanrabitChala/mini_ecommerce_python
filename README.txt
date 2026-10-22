MINISHOP FRONTEND SETUP

1. Copy web.py into the same folder as main.py.
2. Copy templates/ and static/ into that same folder.
3. Install:
   pip install jinja2 python-multipart itsdangerous pwdlib[argon2]
4. Update main.py:
   import os
   from starlette.middleware.sessions import SessionMiddleware
   from web import router as web_router

   After creating app = FastAPI(...), add:
   app.add_middleware(
       SessionMiddleware,
       secret_key=os.getenv("AUTH_SECRET_KEY", "change-this-development-secret"),
       same_site="lax",
       https_only=False
   )
   app.include_router(web_router)

5. Remove the old @app.get("/") route because web.py provides the home page.
6. Keep your existing /users, /products and /orders API routers included.
7. Run: uvicorn main:app --reload
8. Open http://127.0.0.1:8000

This expects the existing models to have:
User: id, username, email, hashed_password, is_admin
Product: id, name, description, price, stock
Order: id, user_id, status, created_at
OrderItem: order_id, product_id, quantity, unit_price

Use the same AUTH_SECRET_KEY for session middleware and your app's token settings where possible.
This is a starter frontend. Before production deployment, add CSRF protection, rate limiting,
HTTPS-only cookies, and stronger error handling. Test checkout with sample products first.
