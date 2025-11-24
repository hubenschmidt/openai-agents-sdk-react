import logging
import os
from typing import Any

from agents import Agent, Runner
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from agent.models import EmailParams, WorkerResult
from agent.prompts import EMAIL_WORKER_PROMPT
from agent.workers.base import BaseWorker

logger = logging.getLogger(__name__)


class EmailWorker(BaseWorker):
    """Worker that sends emails using SendGrid."""

    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY", "")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@example.com")
        self.agent = Agent(
            name="EmailWorker",
            instructions=EMAIL_WORKER_PROMPT,
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )

    def _send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        """Send email via SendGrid API."""
        if not self.api_key:
            return {"success": False, "error": "SENDGRID_API_KEY not configured"}

        message = Mail(
            from_email=self.from_email,
            to_emails=to,
            subject=subject,
            plain_text_content=body,
        )

        try:
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            return {
                "success": True,
                "status_code": response.status_code,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute(
        self,
        task_description: str,
        parameters: dict[str, Any],
        feedback: str | None = None,
    ) -> WorkerResult:
        """Execute email sending task."""
        logger.info("📧 EMAIL_WORKER: Starting execution")
        logger.info(f"   Task: {task_description[:80]}...")
        logger.info(f"   To: {parameters.get('to', 'Not specified')}")
        if feedback:
            logger.info(f"   With feedback from previous attempt")

        try:
            context = f"""Task: {task_description}

Parameters provided:
- To: {parameters.get('to', 'Not specified')}
- Subject: {parameters.get('subject', 'Not specified')}
- Body: {parameters.get('body', 'Not specified')}

{"Previous feedback to address: " + feedback if feedback else ""}

Compose the email and confirm it's ready to send. Return a JSON with to, subject, and body fields."""

            result = await Runner.run(
                self.agent,
                input=context,
            )

            email_content = result.final_output

            email_params = EmailParams(
                to=parameters.get("to", ""),
                subject=parameters.get("subject", ""),
                body=parameters.get("body", email_content),
            )

            logger.info(f"📧 EMAIL_WORKER: Sending to {email_params.to}")
            send_result = self._send_email(
                email_params.to,
                email_params.subject,
                email_params.body,
            )

            if send_result["success"]:
                logger.info(f"✓ EMAIL_WORKER: Sent successfully (status: {send_result['status_code']})")
                return WorkerResult(
                    success=True,
                    output=f"Email sent successfully to {email_params.to}\nSubject: {email_params.subject}\nStatus: {send_result['status_code']}",
                )
            else:
                logger.error(f"❌ EMAIL_WORKER: Send failed: {send_result['error']}")
                return WorkerResult(
                    success=False,
                    output="",
                    error=send_result["error"],
                )

        except Exception as e:
            logger.error(f"❌ EMAIL_WORKER: Failed with error: {e}")
            return WorkerResult(
                success=False,
                output="",
                error=str(e),
            )
