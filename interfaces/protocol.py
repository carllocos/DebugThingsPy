from abc import ABC, abstractmethod

class AMessageTemplate(ABC):


    def __init__(self, **kwargs):
        super().__init__()
        args = ['name']

        for a in args:
            if not kwargs[a]:
                raise ValueError(f'{a} arg missing')

        self.__name = kwargs['name']
        self.reply_template = kwargs.get('reply_template', False)
        self.start = kwargs.get('start', False)
        self.end = kwargs.get('end', False)
        self.payload = kwargs.get('payload', False)
        self.answer = kwargs.get('answer', False)
        self.to_send = kwargs.get('to_send', True)

    def expects_reply(self):
        return self.reply_template and True

    def receive_answer(self, ans):
        self.answer = ans

    def has_start(self):
        return self.start and True

    def has_end(self):
        return self.end and True

    def set_reply_template(self, msg_templ):
        self.reply_template = msg_templ

    def is_to_send(self):
        return self.to_send

