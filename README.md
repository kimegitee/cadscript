AutoCAD Script
==============

Make writing AutoCAD script less error-prone

Usage
-----

Make sure accoreconsole.exe is in PATH.

Build AutoCAD script by chaining method calls
```python
from autocad import AutoCAD
command = AutoCAD().import_(input).export(output).erase().purge()
```

Excecute command via accoconsole.exe

```python
command.exec()
```
