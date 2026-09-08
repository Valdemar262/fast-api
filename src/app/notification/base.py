from abc import ABC, abstractmethod

from app.tasks.mail import send_email_task


class BaseNotification(ABC):
    @abstractmethod
    def subject(self) -> str: ...

    @abstractmethod
    def body(self) -> str: ...

    def send(self, to: str) -> None:
        send_email_task.delay(to=to, subject=self.subject(), body=self.body())
