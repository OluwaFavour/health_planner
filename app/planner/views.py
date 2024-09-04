import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Request,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from fastapi.responses import JSONResponse, HTMLResponse

from sqlalchemy.ext.asyncio import AsyncSession


from .openai_client import OpenAIClient

from ..auth.crud import get_user_by_id
from ..auth.dependencies import get_current_active_user
from ..core.config import get_settings
from ..core.utils import create_jwt_token, verify_jwt_token
from .crud import (
    create_plan,
    create_question,
    get_plan as get_plan_crud,
    get_plans_by_user_id,
)
from ..db.config import get_async_session
from ..db.enums import PlanType
from ..db.models import User as UserModel, Question as QuestionModel
from .openai_client import get_openai_client
from .schemas import Plan as PlanSchema
from .questions import load_questions


router = APIRouter(prefix="/planner", tags=["planner"])


@router.get(
    "/get-ws-token",
    summary="Get a WebSocket token",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {"application/json": {"example": {"message": "Unauthorized"}}},
        },
        status.HTTP_200_OK: {
            "description": "WebSocket token",
            "content": {
                "application/json": {
                    "example": {
                        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVWE9.eyJzdWIiOiJiNDViMTYwYi0yMTM0LTRlNWYtYWRkZC0yNjNhNDNmMDg0YzAiLCJzY29wZXMiOlsid2Vic29ja2V0Il0sImV4cCI6MTcyNjAzNDMxMn0.gp-t5khHsWBI9Z1iRtZOR9mnfEL1jASCKv9INL6wzlQ"
                    }
                }
            },
        },
    },
)
async def get_ws_token(
    user: Annotated[UserModel | None, Depends(get_current_active_user)]
):
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Unauthorized"},
        )

    token = create_jwt_token(
        {"sub": str(user.id), "scopes": ["websocket"]},
        get_settings().jwt_secret_key,
        get_settings().jwt_expires_in_days,
    )

    return {"token": token}


@router.get("/{token}", summary="Chat with the planner", response_class=HTMLResponse)
async def get(token: Annotated[str, Path(title="WebSocket Token")]):
    html = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Chat</title>
        </head>
        <body>
            <h1>WebSocket Chat</h1>
            <form action="" onsubmit="sendMessage(event)">
                <input type="text" id="messageText" autocomplete="off"/>
                <button>Send</button>
            </form>
            <ul id='messages'>
            </ul>
            <script>
                var ws = new WebSocket("ws://127.0.0.1:8000/planner/ws/{token}");
                ws.onmessage = function(event) {{
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                }};
                function sendMessage(event) {{
                    var input = document.getElementById("messageText")
                    ws.send(input.value)
                    input.value = ''
                    event.preventDefault()
                }}
            </script>
        </body>
    </html>
    """
    return HTMLResponse(html)


@router.get(
    "/plans/",
    summary="Get all plans for the authenticated user",
    response_model=list[PlanSchema],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {"application/json": {"example": {"message": "Unauthorized"}}},
        }
    },
)
async def get_plans(
    user: Annotated[UserModel | None, Depends(get_current_active_user)],
    async_session: Annotated[AsyncSession, Depends(get_async_session)],
):
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Unauthorized"},
        )

    plans = await get_plans_by_user_id(async_session, user.id)
    return plans


@router.get(
    "/plans/{plan_id}",
    summary="Get a plan by ID",
    response_model=PlanSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized",
            "content": {"application/json": {"example": {"message": "Unauthorized"}}},
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Plan not found",
            "content": {"application/json": {"example": {"message": "Plan not found"}}},
        },
    },
)
async def get_plan(
    plan_id: Annotated[str, Path(title="Plan ID", description="The ID of the plan")],
    user: Annotated[UserModel | None, Depends(get_current_active_user)],
    async_session: Annotated[AsyncSession, Depends(get_async_session)],
):
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Unauthorized"},
        )

    plan = await get_plan_crud(async_session, plan_id)
    if plan is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Plan not found"},
        )

    return plan


@router.websocket("/ws/{token}", name="planner")
async def planner(
    websocket: WebSocket,
    token: Annotated[str, Path(title="Authorization Token")],
    async_session: Annotated[AsyncSession, Depends(get_async_session)],
):
    payload = verify_jwt_token(token, get_settings().jwt_secret_key)
    if "error" in payload:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason=payload["error"]
        )
        return
    scopes = payload["scopes"]
    if "websocket" not in scopes:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Missing required scope: websocket",
        )
        return
    user_id = UUID(payload["sub"])
    user = await get_user_by_id(async_session, user_id)

    await websocket.accept()

    # Initialize the OpenAI client
    openai_client = get_openai_client()

    try:
        while True:
            # Send a welcome message to the user, asking them to provide a meal plan or workout plan
            await websocket.send_text(
                "Welcome to the planner! Can I help you with a meal plan or workout plan or both?"
            )

            data = await websocket.receive_text()

            # Process the received message here to determine if it's a meal plan, workout plan, or both
            # and then send the appropriate response back to the client
            try:
                choice = await asyncio.to_thread(openai_client.get_plan_choice, data)
                if choice.value == PlanType.MEAL:
                    response = await handle_meal_plan(
                        websocket, openai_client, user, async_session
                    )
                elif choice.value == PlanType.WORKOUT:
                    response = await handle_workout_plan(
                        websocket, openai_client, user, async_session
                    )
                elif choice.value == PlanType.BOTH:
                    response = await handle_both_plans(
                        websocket, openai_client, user, async_session
                    )

                await websocket.send_text(response)
            except ValueError as e:
                await websocket.send_text(str(e))
                break
    except WebSocketDisconnect as e:
        print(f"WebSocketDisconnect: {e}")
    except WebSocketException as e:
        print(f"WebSocketException: {e}")
    finally:
        await websocket.close(status.WS_1001_GOING_AWAY, "Connection closed")


async def handle_meal_plan(
    websocket: WebSocket,
    openai_client: OpenAIClient,
    user: UserModel,
    async_session: AsyncSession,
) -> str:
    # load questions from the database or a file
    question_objects = load_questions(plan_type="meal")

    # Process the request for a meal plan here
    answers = {}
    questions: list[QuestionModel] = []
    for question_object in question_objects:
        await websocket.send_text(
            f"{question_object['question']}\nPurpose: {question_object['purpose']}"
        )
        answer = await websocket.receive_text()
        answers[question_object["question"]] = answer
        question = await create_question(
            async_session=async_session,
            user_id=user.id,
            question=question_object["question"],
            answer=answer,
        )
        questions.append(question)

    try:
        # Process the answers and generate a meal plan here
        plan_description = await asyncio.to_thread(
            openai_client.generate_meal_plan, answers
        )
        plan = await create_plan(
            async_session=async_session,
            user_id=user.id,
            description=plan_description,
            plan_type=PlanType.MEAL,
        )
        # Tag the questions with the plan ID
        for question in questions:
            question.plan_id = plan.id
        await async_session.commit()

        # Return the generated meal plan description
        return plan_description
    except ValueError as e:
        raise e


async def handle_workout_plan(
    websocket: WebSocket,
    openai_client: OpenAIClient,
    user: UserModel,
    async_session: AsyncSession,
) -> str:
    # load questions from the database or a file
    question_objects = load_questions(plan_type="workout")

    # Process the request for a workout plan here
    answers = {}
    questions: list[QuestionModel] = []
    for question_object in question_objects:
        await websocket.send_text(
            f"{question_object['question']}\nPurpose: {question_object['purpose']}"
        )
        answer = await websocket.receive_text()
        answers[question_object["question"]] = answer
        question = await create_question(
            async_session=async_session,
            user_id=user.id,
            question=question_object["question"],
            answer=answer,
        )
        questions.append(question)

    # Process the answers and generate a workout plan here
    try:
        plan_description = await asyncio.to_thread(
            openai_client.generate_workout_plan, answers
        )
        plan = await create_plan(
            async_session=async_session,
            user_id=user.id,
            description=plan_description,
            plan_type=PlanType.WORKOUT,
        )
        # Tag the questions with the plan ID
        for question in questions:
            question.plan_id = plan.id
        await async_session.commit()

        return plan_description
    except ValueError as e:
        raise e


async def handle_both_plans(
    websocket: WebSocket,
    openai_client: OpenAIClient,
    user: UserModel,
    async_session: AsyncSession,
) -> str:
    # Send a message to the user to provide answers for both meal and workout plans
    await websocket.send_text("Please provide answers for both meal and workout plans.")

    try:
        meal_plan = await handle_meal_plan(
            websocket, openai_client, user, async_session
        )
        workout_plan = await handle_workout_plan(
            websocket, openai_client, user, async_session
        )
        return f"# Meal Plan:\n{meal_plan}\n\n# Workout Plan:\n{workout_plan}"
    except ValueError as e:
        raise e
