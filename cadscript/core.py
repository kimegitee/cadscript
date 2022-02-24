from pexpect.popen_spawn import PopenSpawn
from pathlib import Path
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
        return self._append(f'IMPORT "{path}"\n')
    def export(self, path:str):
        self._append(f'EXPORT "{path}" all\n\n')
        return self._cancel_sequence()
    def open(self, path:str):
        return self._exec_utf8(f'open "{path}"\n')
    def to_dxf(self, path:str=None, overwrite=False):
        path = '' if path is None else f'"{path}"'
        overwrite = 'Y' if overwrite else 'N'
        return self._exec_utf8(f'saveas dxf 16 {path} {overwrite}\n')
    def stlout(self, path:str):
        return self._append(f'STLOUT all\n\n\n"{path}"\n(command)\n')
    def erase(self):
        return self._append('ERASE all\n\n')
    def purge(self):
        return self._append(f'-PURGE all * n\n')
    def terminate(self):
        self.p.kill(signal.SIGTERM)
        self.terminated = True
    def _return(self, command):
        command = command.split(' ')[0]
        ok = f'Command: {command}.*Command:'
        confirm = f'Command: {command}.*<[YN]>.*'
        error = '\**MessageBox.*'
        status = self.p.expect([ok, confirm, error], timeout=5)
        if status == 2:
            self.p.send('\x1b')
            raise(RuntimeError('\n' + self.p.after))
        else:
            print(self.p.after)
        return self
    def _assert_running(self):
        assert not self.terminated, 'Program has already been terminated'
    def _exec(self, command):
        self._assert_running()
        self.p.send(command)
        return self._return(command)
    def _exec_utf8(self, command):
        '''Send utf8 encoded command to AutoCAD for execution'''
        self._assert_running()
        with tempfile.NamedTemporaryFile('w+', suffix='.scr', delete=False, encoding='utf-8-sig') as file:
            file.write(command)
            file.close() # On Windows file has to be closed before being opened again
            self.p.send(f'script "{file.name}"\n')
            return self._return(command)
