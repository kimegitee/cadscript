AutoCAD Scripter
================

Make writing AutoCAD script less error-prone

Usage
-----

Make sure accoreconsole.exe is in PATH.

Build AutoCAD script by method chaining. A simple pipeline to convert different CAD formats can be built like so

```python
from cadscript import Command
command = Command().import_(input).export(output).erase().purge()
```

Excecute command via accoconsole.exe

```python
command.exec()
```
