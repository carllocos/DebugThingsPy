class AMessage():
    def __init__(self, content, reply=None):
        self.__content = content
        self.__reply = reply

    def has_reply(self):
        return self.__reply is not None

    def get_reply(self, aSerializer, sock):
        f = self.__reply
        return f(aSerializer, sock)

    @property
    def content(self):
        return self.__content
