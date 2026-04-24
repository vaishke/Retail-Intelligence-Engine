from services.session_service import (
    add_message,
    get_session,
    create_session,
    update_session,
    end_session,
    delete_session,
    save_durable_graph_context,
)
from sales_graph.graph import run_sales_graph
from db.database import sessions_collection

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from services.user_auth_service import verify_token

router = APIRouter(
    prefix="/sales",
    tags=["Sales Agent"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


class ResponseWrapper:
    def __init__(self, response_dict):
        self.message = response_dict.get("message")
        self.prompt = response_dict.get("prompt")
        for k, v in response_dict.items():
            if k not in ["message", "prompt"]:
                setattr(self, k, v)


@router.post("/chat")
def sales_chat(
    payload: dict = Body(...),
    user=Depends(get_current_user)
):
    try:
        user_id = user["user_id"]
        session_id = payload.get("session_id")
        user_message = payload.get("message")

        if not session_id:
            raise HTTPException(status_code=400, detail="session_id required")

        if not user_message or not user_message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        session = get_session(session_id)
        if not session or session["user_id"] != user_id:
            print("SESSION USER ID:", session["user_id"])
            print("TOKEN USER ID:", user["user_id"])
            raise HTTPException(status_code=403, detail="Unauthorized")

        add_message(session_id, "user", user_message)

        result = run_sales_graph(
            user_id=user_id,
            session_id=session_id,
            channel=payload.get("channel", "web").lower(),
            message=user_message,
            extras=payload.get("extras")
        )

        save_durable_graph_context(session_id, result)

        bot_reply = result.get("response", {}).get("message", "")

        add_message(session_id, "assistant", bot_reply, payload=result.get("response", {}))

        return {
            "success": True,
            "response": ResponseWrapper(result.get("response", {})),
            "state": result
        }

    except Exception as e:
        print("CHAT ERROR:", str(e))
        raise e


@router.post("/session/start")
def start_session(
    data: dict = Body(...),
    user=Depends(get_current_user)
):
    user_id = user["user_id"]
    channel = data.get("channel", "WEB")

    return create_session(user_id, channel)


@router.get("/session/{session_id}")
def get_session_route(
    session_id: str,
    user=Depends(get_current_user)
):
    session = get_session(session_id)

    if not session or session["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return session


@router.post("/session/update/{session_id}")
def update_session_route(
    session_id: str,
    data: dict = Body(...),
    user=Depends(get_current_user)
):
    session = get_session(session_id)

    if not session or session["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return update_session(session_id, data)


@router.post("/session/end/{session_id}")
def end_session_route(
    session_id: str,
    user=Depends(get_current_user)
):
    session = get_session(session_id)

    if not session or session["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return {"success": end_session(session_id)}


@router.get("/sessions")
def get_user_sessions(user=Depends(get_current_user)):
    user_id = user["user_id"]

    sessions = list(
        sessions_collection.find(
            {"user_id": user_id, "status": {"$ne": "deleted"}}
        ).sort("metadata.last_updated", -1)
    )

    for s in sessions:
        s["_id"] = str(s["_id"])

    return sessions


@router.delete("/session/{session_id}")
def delete_session_route(
    session_id: str,
    user=Depends(get_current_user)
):
    session = get_session(session_id)

    if not session or session["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return {"success": delete_session(session_id)}
