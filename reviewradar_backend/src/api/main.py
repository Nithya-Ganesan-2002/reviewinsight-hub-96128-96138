from fastapi import FastAPI, HTTPException, Depends, Path, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any

# ----------------------------
# App metadata for OpenAPI docs
# ----------------------------
app = FastAPI(
    title="ReviewRadar Backend API",
    version="0.1.0",
    description=(
        "ReviewRadar backend API provides endpoints for product search, "
        "review aggregation and submission, AI-generated review insights, and user authentication."
    ),
    openapi_tags=[
        {"name": "Products", "description": "Product search, listing, and basic info"},
        {"name": "Reviews", "description": "Product reviews management: aggregate, submit, fetch"},
        {"name": "Insights", "description": "AI-generated review summaries and insights"},
        {"name": "Search", "description": "Full-text product search"},
        {"name": "User", "description": "User account management and authentication"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ----------------------------
# Pydantic Models
# ----------------------------


class Product(BaseModel):
    """Product model for listing and search responses"""

    id: str = Field(..., description="Unique product ID")
    name: str = Field(..., description="Product name")
    brand: Optional[str] = Field(None, description="Brand name")
    image_url: Optional[str] = Field(None, description="Product image URL")
    description: Optional[str] = Field(None, description="Description of the product")
    average_rating: Optional[float] = Field(
        None, description="Aggregated average rating"
    )
    review_count: Optional[int] = Field(
        None, description="Total number of aggregated reviews"
    )


class Review(BaseModel):
    """Product review submitted by users or aggregated from 3rd-parties"""

    id: Optional[str] = Field(None, description="Review ID")
    product_id: str = Field(..., description="Product ID")
    user_name: Optional[str] = Field(None, description="Display name of reviewer")
    rating: int = Field(
        ..., ge=1, le=5, description="Rating from 1 to 5"
    )
    source: Optional[str] = Field(
        None, description="Source of review (user, Trustpilot, Amazon, etc.)"
    )
    title: Optional[str] = Field(None, description="Short title for review")
    content: str = Field(..., description="Text content of the review")
    created_at: Optional[str] = Field(
        None, description="ISO timestamp review was written"
    )


class ReviewSubmission(BaseModel):
    """POST payload for user-submitted product reviews"""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    title: Optional[str] = Field(None, description="Short title for review")
    content: str = Field(..., description="Review text")


class Insight(BaseModel):
    """AI-generated insight or summary for a product's reviews"""

    product_id: str = Field(..., description="Product ID")
    summary: str = Field(..., description="Short summary of product sentiment/insight")
    highlights: Dict[str, Any] = Field(
        ..., description="Key points or themes extracted from reviews"
    )


class User(BaseModel):
    """App user for authentication and review tracking"""

    username: str = Field(..., description="Unique username")
    email: EmailStr = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="User full name")


class Token(BaseModel):
    """OAuth2 token model"""

    access_token: str
    token_type: str


# Demo in-memory stores (to be replaced by real database/integrations)
MOCK_PRODUCTS = [
    Product(
        id="prod_1",
        name="Widget 3000",
        brand="WidgCo",
        image_url="https://example.com/img/widget3000.jpg",
        description="An innovative widget",
        average_rating=4.2,
        review_count=127,
    ),
    Product(
        id="prod_2",
        name="Gadget Ultra",
        brand="Gadgetron",
        image_url="https://example.com/img/gadget_ultra.jpg",
        description="High-end gadget",
        average_rating=3.8,
        review_count=87,
    ),
]

MOCK_REVIEWS = [
    Review(
        id="r1",
        product_id="prod_1",
        user_name="Ava",
        rating=5,
        source="user",
        title="Amazing widget",
        content="Best widget ever used!",
        created_at="2024-07-01T14:20:00",
    )
]


# ----------------------------
# HEALTH CHECK
# ----------------------------


# PUBLIC_INTERFACE
@app.get("/", tags=["User"])
def health_check():
    """Health check endpoint for backend"""
    return {"message": "Healthy"}


# ----------------------------
# AUTHENTICATION ENDPOINTS
# ----------------------------
# These are placeholder/demonstration implementations


# PUBLIC_INTERFACE
@app.post(
    "/token",
    response_model=Token,
    summary="User login (token generation)",
    tags=["User"],
)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticates a user and returns an access token.
    Replace with real authentication for production!
    """
    # Demo: anyone gets a fixed token
    if not form_data.username:
        raise HTTPException(status_code=400, detail="Username required")
    return {
        "access_token": f"demo-token-for-{form_data.username}",
        "token_type": "bearer"
    }


# ----------------------------
# PRODUCT ENDPOINTS
# ----------------------------


# PUBLIC_INTERFACE
@app.get(
    "/products",
    response_model=List[Product],
    summary="List all products",
    tags=["Products"],
)
def list_products():
    """
    List available products with summary info.
    """
    return MOCK_PRODUCTS


# PUBLIC_INTERFACE
@app.get(
    "/products/{product_id}",
    response_model=Product,
    summary="Get product by ID",
    tags=["Products"],
)
def get_product(product_id: str = Path(..., description="Product ID")):
    """
    Returns product details for a given product ID.
    """
    for prod in MOCK_PRODUCTS:
        if prod.id == product_id:
            return prod
    raise HTTPException(status_code=404, detail="Product not found")


# PUBLIC_INTERFACE
@app.get(
    "/search",
    response_model=List[Product],
    summary="Search products",
    tags=["Search"],
)
def search_products(q: str = Query(..., description="Product name or keyword to search")):
    """
    Searches for products whose names contain the query string.
    """
    return [p for p in MOCK_PRODUCTS if q.lower() in p.name.lower()]


# ----------------------------
# REVIEW ENDPOINTS
# ----------------------------


# PUBLIC_INTERFACE
@app.get(
    "/products/{product_id}/reviews",
    response_model=List[Review],
    summary="Get reviews for a product",
    tags=["Reviews"],
)
def get_product_reviews(product_id: str):
    """
    Gets all reviews (user and aggregated) for a product.
    In real implementation, aggregates from local DB + Trustpilot/Amazon APIs.
    """
    return [r for r in MOCK_REVIEWS if r.product_id == product_id]


# PUBLIC_INTERFACE
@app.post(
    "/products/{product_id}/reviews",
    response_model=Review,
    status_code=status.HTTP_201_CREATED,
    summary="Submit new product review",
    tags=["Reviews"],
)
def submit_review(
    product_id: str,
    review: ReviewSubmission,
    token: str = Depends(oauth2_scheme),
):
    """
    Allows an authenticated user to submit a new review for a product.
    """
    new_review = Review(
        id="r_user_" + product_id,
        product_id=product_id,
        user_name="TestUser",  # In production: get from user/token
        rating=review.rating,
        source="user",
        title=review.title,
        content=review.content,
        created_at="2024-07-05T10:00:00"
    )
    MOCK_REVIEWS.append(new_review)
    return new_review


# ----------------------------
# INSIGHT (AI) ENDPOINTS
# ----------------------------


# PUBLIC_INTERFACE
@app.get(
    "/products/{product_id}/insights",
    response_model=Insight,
    summary="AI-generated review insights for a product",
    tags=["Insights"],
)
def get_product_insights(
    product_id: str = Path(..., description="Product ID"),
):
    """
    Returns AI-generated summary insights about a product's reviews.
    (Stub; integrate with OpenAI or LLM service in future.)
    """
    # Placeholder logic; return demo data
    summary = (
        f"This product ({product_id}) is generally well-rated. "
        "Most users praise its quality and value."
    )
    highlights = {
        "pros": ["Great quality", "Worth the price"],
        "cons": ["Available in limited colors"]
    }
    return Insight(product_id=product_id, summary=summary, highlights=highlights)

# Additional endpoints (e.g., user registration, etc.) can be added here.
