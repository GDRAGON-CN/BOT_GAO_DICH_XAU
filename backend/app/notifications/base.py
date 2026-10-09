from abc import ABC, abstractmethod

class INotificationService(ABC):
    @abstractmethod
    async def send_message(self, text: str) -> bool:
        pass

    @abstractmethod
    def notify_async(self, text: str) -> None:
        pass
