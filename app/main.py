from fastapi import FastAPI

app = FastAPI(title="Futurisys API")

# @app.get("/")
# async def root():
#     return {"message": "Hello World"}

# @app.get("/")
# def root():
#     return {"status": "ok"}


# @app.get("/health")
# def health():
#     return {"status": "healthy"}

@app.get("/hello")
def hello(name: str):
    return {"message": f"Hello {name}"}

# so if app is deployed, and another service calls:
# GET /hello?name=Alice
# we get : "message": "Hello Alice"


from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str

user = User(
    name="Alice",
    age=32,
    email="alice@example.com"
)

## if we mix them:

class UserType(BaseModel):
    name: str
    age: int


@app.post("/users")
def create_user(user: UserType):
    return {
        "message": f"Created {user.name}",
        "age": user.age
    }

#FAST API receives HTTP request, FastAPI gives function a proper User object

