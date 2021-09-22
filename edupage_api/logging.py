from enum import Enum, auto
from datetime import date, datetime
from colorama import Fore
import time

import colorama

class LogLevel(Enum):
    NONE = "NONE"
    DEBUG = "DEBUG"
    WARNING = "WARNING"
    ERROR = "ERROR"

class Logger:
    def __init__(self, level: LogLevel, color: bool):
        self.level = level
        self.last_log_time = time.time()
        self.color = color

    def __log(self, level, message):      
        if self.level == LogLevel.DEBUG or self.level == LogLevel.ERROR:
            pass
        elif self.level == LogLevel.WARNING and level == LogLevel.WARNING or level == LogLevel.ERROR:
            pass
        else:
            return

        time_since_last_log = round((time.time() - self.last_log_time) * 1000.0)
        self.last_log_time = time.time()

        

        s = f"{message}"

        if self.color:
            color = None
            if level == LogLevel.WARNING:
                color = f"{Fore.YELLOW}[!] "
            elif level == LogLevel.ERROR:
                color = f"{Fore.RED}[E] "
            elif level == LogLevel.DEBUG:
                color = "[-] "
            
            if color != None:
                s = f"{color}{message}"

        if not self.color:
            s = f"[{level.value}] {s}"

        if time_since_last_log != 0:
            s += f" +{time_since_last_log}ms"
        
        if self.color:
            s += Fore.RESET

        print(s)

    def debug(self, message):
        self.__log(LogLevel.DEBUG, message)
    
    def warning(self, message):
        self.__log(LogLevel.WARNING, message)
    
    def error(self, message):
        self.__log(LogLevel.ERROR, message)
    
    
    