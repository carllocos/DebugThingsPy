# import inspect
# import psutil

# DEBUG = False
# def dbgprint(s):
#     curframe = inspect.currentframe()
#     calframe = inspect.getouterframes(curframe, 2)
#     cn =str(calframe[1][3])
#     if DEBUG:# and cn in ONLY:
#         print((cn + ':').upper(), s)


# class LocDevice():

#     def __init__(self, proc):
#         self.__process = proc

#     @property
#     def process(self):
#         return self.__process

# def find_device(config):
#     name = config['name']
#     dbgprint(f"Searching for {name} process")
#     WDProcess = None
#     for p in psutil.process_iter(['pid','name', 'username']):
#         if p.info.get('name') == name:
#             WDProcess = LocDevice(p)
#             dbgprint(f'found process {WDProcess.process.info}')
#             break

#     return WDProcess
