AutoCAD Scripter
================

Make writing AutoCAD script less error-prone

Usage
-----

Make sure accoreconsole.exe is in PATH.

Build AutoCAD script by method chaining. A simple pipeline to convert DWG to DXF can be built like so

```python
from cadscript import Program

with Program() as p:
    p.open(input).to_dxf(overwrite=True)
```
