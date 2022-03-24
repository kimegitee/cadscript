from pexpect.popen_spawn import PopenSpawn
from pexpect import TIMEOUT
from pathlib import Path
from typing import Literal as either
import os
import signal
import tempfile

class Program:
    '''Wrapper to generate AutoCAD script

    Each method corresponds to an AutoCAD command of the same name, except when
    such commands conflict with Python keywords, such as `import_` below.
    '''
    def __init__(self, s=[]):
        self.p = PopenSpawn('accoreconsole.exe', encoding='utf-16-le')
        self.p.expect('.*Command:.*:.*:.*', timeout=None)
        print(self.p.after)
        self.terminated = False
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self.terminate()
    def _append(self, s:str):
        self.s.append(s)
        return self
    def _cancel_sequence(self):
        '''Add sequence to end infinite input loop'''
        self.s += '(progn (if (> (getvar "cmdactive") 0) (command)) (princ))\n'
        return self
    def import_(self, path:str):
        path = Path(path).resolve()
        return self._exec_utf8(f'import "{path}"\n')
    def export(self, path:str):
        return self._exec_utf8(f'export "{path}" all\n\n')
    def open(self, path:str):
        return self._exec_utf8(f'open "{path}"\n')
    def to_dxf(self, path:str=None, format:either['binary', 'text']='text', overwrite=False):
        path = '' if path is None else f'"{path}"'
        format = 'B' if format == 'binary' else '16'
        overwrite = 'Y' if overwrite else 'N'
        return self._exec_utf8(f'saveas dxf {format} {path} {overwrite}\n')
    def stlout(self, path:str):
        return self._append(f'STLOUT all\n\n\n"{path}"\n(command)\n')
    def erase(self):
        return self._exec('ERASE all\n\n')
    def purge(self):
        return self._exec(f'-purge all *\nn\n')
    def terminate(self):
        self.p.kill(signal.SIGTERM)
        self.terminated = True
    def _return(self, command, ok, error):
        command = command.split(' ')[0]
        if ok is None:
            ok = f'Command: {command}.*Command:'
            confirm = f'Command: {command}.*<[YN]>.*Command:'
            ok = [ok, confirm]
        if error is None:
            error = ['\**MessageBox.*', '\*Invalid selection.*', TIMEOUT]
        status = self.p.expect(ok + error, timeout=120)
        if status in [2, 3]:
            self.p.send('\x1b')
            raise(RuntimeError('\n' + self.p.after))
        elif status == 4:
            self.p.send('\x1b')
            raise(RuntimeError('\n' + self.p.before))
        else:
            print(self.p.after)
        return self
    def _assert_running(self):
        assert not self.terminated, 'Program has already been terminated'
    def _exec(self, command, ok=None, error=None):
        self._assert_running()
        self.p.send(command + 'gibberish\n')
        return self._return(command, ok, error)
    def _exec_utf8(self, command, ok=None, error=None):
        '''Send utf8 encoded command to AutoCAD for execution'''
        self._assert_running()
        with tempfile.NamedTemporaryFile('w+', suffix='.scr', delete=False, encoding='utf-8-sig') as file:
            file.write(command + 'gibberish\n')
            file.close() # On Windows file has to be closed before being opened again
            self.p.send(f'script "{file.name}"\n')
            return self._return(command, ok, error)
