from rich.console import Console
from rich.text import Text
import datetime

def timestamp() -> Text:
        return Text(datetime.datetime.now().isoformat(sep=" ", timespec="milliseconds"), style="dim italic")

class ConsoleLogger:
    def __init__(self, verbose: bool, prefix: str = "MAIN"):
        self.verbose = verbose
        self.console = Console() 
        self.prefix = prefix

    def log(self, text: str):
        if self.verbose: self.console.print(timestamp(), " INFO ", "[" + self.prefix + "] " + text)

    def logerr(self, text: str):
        if self.verbose: self.console.print(timestamp(), " [red]FAIL[/red] ", "[" + self.prefix + "] " + text)

    def logwarn(self, text: str):
        if self.verbose: self.console.print(timestamp(), " [yellow]WARN[/yellow] ", "[" + self.prefix + "] " + text)

    def logok(self, text: str):
        if self.verbose: self.console.print(timestamp(), "  [green]OK[/green]  ", "[" + self.prefix + "] " + text)

    def printjson(self, json: str):
        if self.verbose: self.console.print_json(json)