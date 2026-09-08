import pytest

from app.tasks.mail import send_email_task


def test_the_task_sends_the_email(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[dict[str, str]] = []

    async def fake_send(*, to: str, subject: str, body: str) -> None:
        sent.append({"to": to, "subject": subject, "body": body})

    monkeypatch.setattr("app.tasks.mail.send_email", fake_send)

    send_email_task(to="user@example.com", subject="Hello", body="Body text")

    assert sent == [{"to": "user@example.com", "subject": "Hello", "body": "Body text"}]


def test_a_transport_failure_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_send(*, to: str, subject: str, body: str) -> None:
        raise ConnectionError("SMTP unavailable")

    monkeypatch.setattr("app.tasks.mail.send_email", failing_send)

    with pytest.raises(ConnectionError):
        send_email_task(to="user@example.com", subject="Hello", body="Body text")
