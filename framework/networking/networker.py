import pygame
from typing import Any, TypedDict, Callable
from types import SimpleNamespace


class Networker:
    NETWORK_RECEIVE_EVENT = pygame.event.custom_type()
    NETWORK_ERROR_EVENT = pygame.event.custom_type()
    NETWORK_CONNECTION_EVENT = pygame.event.custom_type()
    NETWORK_DISCONNECT_EVENT = pygame.event.custom_type()
    NETWORK_CLOSE_EVENT = pygame.event.custom_type()

    def __init__(self, core_object_reference : "Core") -> None:
        global core_object
        core_object = core_object_reference
        self.core : "Core" = core_object
        self.NETWORK_LOCALSTORAGE_KEY : str = "tmp_recv"
        if "networking" not in self.core.js_source:
            self.core.load_js_source_file("framework/networking/networking.js", "networking", 
                                            {"PEERID" : None, "IS_HOST" : None, "NETWORK_KEY" : None})
        if "sendnetmessage" not in self.core.js_source:
            self.core.load_js_source_file("framework/networking/network_send_event_dispatcher.js", "sendnetmessage", 
                                            {"DATA" : None})
        
    def update_network_recv(self):
        mods : dict[str, Callable[[SimpleNamespace], None]] = {
            "" : self.on_data_received,
            "err" : self.on_network_error,
            "conn" : self.on_network_connection,
            "close" : self.on_network_close,
            "dc" : self.on_network_disconnect
        }
        for mod in mods:
            curr_recv : str|None = self.core.storage.get_web(self.NETWORK_LOCALSTORAGE_KEY + mod)
            if curr_recv:
                callback = mods[mod]
                callback(SimpleNamespace(detail=curr_recv))
                self.core.storage.set_web(self.NETWORK_LOCALSTORAGE_KEY + mod, "")
    
    def set_network_key(self, new_key : str):
        if not self.core.is_web(): return
        self.NETWORK_LOCALSTORAGE_KEY = new_key
        self.core.storage.set_web(self.NETWORK_LOCALSTORAGE_KEY, "")
        
    
    def on_data_received(self, event : SimpleNamespace):
        #print(event.detail)
        pygame.event.post(pygame.Event(self.NETWORK_RECEIVE_EVENT, {'data' : event.detail}))

    def on_network_error(self, event : SimpleNamespace):
        #print(event.detail)
        pygame.event.post(pygame.Event(self.NETWORK_ERROR_EVENT, {'info' : event.detail}))

    def on_network_connection(self, event : SimpleNamespace):
        pygame.event.post(pygame.Event(self.NETWORK_CONNECTION_EVENT, {}))

    def on_network_close(self, event : SimpleNamespace):
        pygame.event.post(pygame.Event(self.NETWORK_CLOSE_EVENT, {}))

    def on_network_disconnect(self, event : SimpleNamespace):
        pygame.event.post(pygame.Event(self.NETWORK_DISCONNECT_EVENT, {}))

    def send_network_message(self, data : str) -> bool:
        return self.core.run_js_source_file("sendnetmessage", {"DATA" : data})

    def update(self):
        if self.core.is_web():
            self.update_network_recv()
    
    def __hints(self):
        global Core
        from framework.core.core import Core, JsSource

