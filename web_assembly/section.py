# from __future__ import annotations
# from typing import TypeVar, Generic, Union, Any

# T = TypeVar('T')

# class Section(Generic[T]):

#     def __init__(self, content: T, start: int, end: int, count: Union[int, None] = None):
#         self.__start = start
#         self.__end = end
#         self.__count = count
#         self.__content = content

#     @property
#     def content(self) -> T:
#         return self.__content
    
#     @content.setter
#     def content(self, _: Any):
#         raise ValueError("Section's content cannot be changed")