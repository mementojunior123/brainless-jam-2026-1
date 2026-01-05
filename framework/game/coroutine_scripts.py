from typing import Callable, Generator

CoroutineFunction = Callable[..., Generator]

class CoroutineScript:
    def __init__(self, coroutine : CoroutineFunction|None = None):
        self.initialized : bool = False
        self.is_over : bool = False
        self.coro_func : CoroutineFunction = coroutine or self.corou
        self.coroutine : Generator = None
        self.coro_attributes : list[str] = []

    def type_hints(self):
        self.coro_attributes = []
    
    def initialize(self, *args, **kwargs):
        self.coroutine = self.coro_func(*args, **kwargs)
        next(self.coroutine)
        self.initialized = True

    def process_frame(self, values = None):
        if self.is_over : return
        if not self.initialized: self.initialize()
        try:
            return self.coroutine.send(values)
        except StopIteration as e:
            self.is_over = True
            return e.value
    
    def __getattr__(self, name : str):
        if name not in self.coro_attributes: raise AttributeError
        return self.coroutine.gi_frame.f_locals[name]
    
    @staticmethod
    def corou(*args, **kwargs) -> Generator:
        raise NotImplementedError
