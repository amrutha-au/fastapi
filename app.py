from fastapi import BackgroundTasks, FastAPI, UploadFile, File, Form
from tortoise.contrib.fastapi import register_tortoise
from models import (
    supplier_pydantic,
    supplier_pydanticIn,
    Supplier,
    product_pydantic,
    product_pydanticIn,
    Product,
)

# email
from typing import List
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, EmailStr
from starlette.responses import JSONResponse

# dotenv
from dotenv import dotenv_values

# credentials
crendentials = dotenv_values(".env")

#addings cors headers
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

#adding cors urls
origins = [
    'http://localhost:3000'
]

#add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

@app.get("/")
def index():
    return {"Msg ": "Go to '/docs' for the API documentation"}


# CRUD functionalities for Supplier Model
@app.post("/supplier")
async def add_supplier(supplier_info: supplier_pydanticIn):
    supplier_obj = await Supplier.create(**supplier_info.dict(exclude_unset=True))
    response = await supplier_pydantic.from_tortoise_orm(supplier_obj)
    return {"status": "ok", "data": response}


@app.get("/supplier")
async def get_all_suppliers():
    response = await supplier_pydantic.from_queryset(Supplier.all())
    return {"status": "ok", "data": response}


@app.get("/supplier/{supplier_id}")
async def get_specific_supplier(supplier_id: int):
    response = await supplier_pydantic.from_queryset_single(
        Supplier.get(id=supplier_id)
    )
    return {"status": "ok", "data": response}


@app.put("/supplier/{supplier_id}")
async def update_supplier(supplier_id: int, update_info: supplier_pydanticIn):
    supplier = await Supplier.get(id=supplier_id)
    update_info = update_info.dict(exclude_unset=True)
    supplier.name = update_info["name"]
    supplier.company = update_info["company"]
    supplier.email = update_info["email"]
    supplier.phone = update_info["phone"]
    await supplier.save()
    response = await supplier_pydantic.from_tortoise_orm(supplier)
    return {"status": "ok", "data": response}


@app.delete("/supplier/{supplier_id}")
async def delete_supplier(supplier_id: int):
    supplier = await Supplier.filter(id=supplier_id).first()
    if supplier:
        await supplier.delete()
        return {"status": "ok"}
    else:
        return {"status": "Supplier not found"}


# CRUD functionalities for Product Model


@app.post("/product/{supplier_id}")
async def add_product(supplier_id: int, products_details: product_pydanticIn):
    supplier = await Supplier.get(id=supplier_id)
    products_details = products_details.dict(exclude_unset=True)
    products_details["revenue"] += (
        products_details["quantity_sold"] * products_details["unit_price"]
    )
    product_obj = await Product.create(**products_details, supplied_by=supplier)
    response = await product_pydantic.from_tortoise_orm(product_obj)
    return {"status": "ok", "data": response}


@app.get("/product")
async def get_all_products():
    response = await product_pydantic.from_queryset(Product.all())
    return {"status": "ok", "data": response}


@app.get("/product/{product_id}")
async def get_specific_product(product_id: int):
    response = await product_pydantic.from_queryset_single(Product.get(id=product_id))
    return {"status": "ok", "data": response}


@app.put("/product/{product_id}")
async def update_product(product_id: int, update_info: product_pydanticIn):
    product = await Product.get(id=product_id)
    update_info = update_info.dict(exclude_unset=True)
    product.name = update_info["name"]
    product.quantity_in_stock = update_info["quantity_in_stock"]
    product.quantity_sold = update_info["quantity_sold"]
    product.unit_price = update_info["unit_price"]
    product.revenue = (
        update_info["quantity_sold"] * update_info["unit_price"]
    ) + update_info["revenue"]
    await product.save()
    response = await product_pydantic.from_tortoise_orm(product)
    return {"status": "ok", "data": response}


@app.delete("/product/{product_id}")
async def delete_product(product_id: int):
    product = await Product.filter(id=product_id).first()
    if product:
        await product.delete()
        return {"status": "ok"}
    else:
        return {"status": "Product not found"}


class EmailSchema(BaseModel):
    email: List[EmailStr]


class EmailContent(BaseModel):
    message: str
    subject: str


conf = ConnectionConfig(
    MAIL_USERNAME=crendentials["EMAIL"],
    MAIL_PASSWORD="jewfdebdknhajkgn",
    MAIL_FROM=crendentials["EMAIL"],
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


@app.post("/email/{product_id}")
async def send_email(product_id: int, content: EmailContent):
    product = await Product.get(id=product_id)
    supplier = await product.supplied_by
    suplier_email = [supplier.email]

    html = f"""
    <h5>Arthya Tech Solutions Private Ltd.</h5>
    <br> 
    <p>{content.message}</p> 
    <br>
    <h6>Best Regards</h6>
    <h6>Arthya Tech Solutions Private Ltd.</h6>    
    """

    message = MessageSchema(
        subject=content.subject, recipients=suplier_email, body=html, subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return {"status": "ok"}


register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
