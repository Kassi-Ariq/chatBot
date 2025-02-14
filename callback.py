from langchain_core.callbacks import BaseCallbackHandler


class AlertCallback(BaseCallbackHandler):
    def __init__(self):
        self.chat_response = None
        self.notification_response = None

    def on_chain_end(self, outputs, **kwargs):
        if isinstance(outputs, dict):
            if outputs["emergency"] == "YES":
                self.chat_response = "🚨Emergency detected! Please call 911 or seek immediate help.🚨"
                self.notification_response = "🚨User needs immediate help."
            elif outputs["swear"] == "YES":
                self.chat_response = "🛑Please avoid using inappropriate language.🛑"
                self.notification_response = "🛑User is using inappropriate language."

    def get_result(self):
        return self.chat_response
    
    def get_notification_result(self):
        return self.notification_response
