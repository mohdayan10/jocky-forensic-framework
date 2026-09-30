"""WebSocket consumers for real-time investigation status streaming."""

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer


class StatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.case_id = self.scope['url_route']['kwargs']['case_id']
        self.group_name = f"case_{self.case_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send initial connection confirmation
        await self.send(json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "case_id": self.case_id,
            "message": "Connected to JOCKY status stream",
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Echo commands back as acknowledgment
        await self.send(json.dumps({"type": "ACK", "received": data}))

    # Handler for group messages broadcast from Django views/Celery tasks
    async def agent_status(self, event):
        await self.send(json.dumps({
            "type": "AGENT_STATUS",
            "host_id": event["host_id"],
            "status": event["status"],
            "artifact_count": event.get("artifact_count", 0),
        }))

    async def evidence_received(self, event):
        await self.send(json.dumps({
            "type": "EVIDENCE_RECEIVED",
            "host_id": event["host_id"],
            "evidence_id": event["evidence_id"],
            "artifact_type": event["artifact_type"],
        }))

    async def finding_raised(self, event):
        await self.send(json.dumps({
            "type": "FINDING_RAISED",
            "finding_id": event["finding_id"],
            "severity": event["severity"],
            "confidence": event["confidence"],
        }))

    async def forge_complete(self, event):
        await self.send(json.dumps({
            "type": "FORGE_COMPLETE",
            "builds": event.get("builds", {}),
        }))

    async def ai_complete(self, event):
        await self.send(json.dumps({
            "type": "AI_COMPLETE",
            "finding_id": event.get("finding_id", ""),
            "status": event.get("status", ""),
        }))

    async def blockchain_verified(self, event):
        await self.send(json.dumps({
            "type": "BLOCKCHAIN_VERIFIED",
            "evidence_id": event.get("evidence_id", ""),
            "verified": event.get("verified", False),
        }))
