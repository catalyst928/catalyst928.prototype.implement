"""CC-server: FastAPI backend — WebRTC signaling relay, A2A orchestrator, Communication Agent."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ws_signal import router as ws_router, get_gui_sender
from order import router as order_router, set_gui_sender
from communication import router as comm_router

app = FastAPI(title="CC-server", version="1.0.0")

# CORS — allow all origins for local demo access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ws_router)
app.include_router(order_router)
app.include_router(comm_router)

# Wire the gui sender to the order module
set_gui_sender(get_gui_sender())


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
