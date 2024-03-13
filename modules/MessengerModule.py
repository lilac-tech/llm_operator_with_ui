import json

class MessageHandler:
    def __init__(self, message_data) -> None:
        self.message = json.loads(message_data)
    
    def get_message_reciepient(self):
        return self.message["receipient"]