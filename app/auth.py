from fastapi import Header, HTTPException, status


async def verify_token(authorization: str | None = Header(default=None)) -> None:
    # if authorization != "Bearer-test-token":
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid or missing bearer token",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    pass
