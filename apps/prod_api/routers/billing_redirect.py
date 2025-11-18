from fastapi import APIRouter

router = APIRouter(prefix="/billing", tags=["Billing"])

# 💰 Price users will pay (INR)
PRICE = 999  # change anytime


@router.get("/pay")
def pay():
    """
    Returns checkout link using your Razorpay.me payment page.
    Your dashboard can simply redirect user to this URL.
    """
    url = f"https://razorpay.me/@pentaprimesolutionsllp?amount={PRICE}"
    return {"checkout_url": url}
