from pexpect.popen_spawn import PopenSpawn
from pathlib import Path
import os
import signal
import tempfile

def run_script(script:str, verbose=True):
    '''Excecute a series of AutoCAD commands in a subprocess

    Requires accoreconsole.exe to be in PATH'''
    # It is important to use utf-8-sig not utf-8 on Windows so that Unicode file names are correctly loaded
    with tempfile.NamedTemporaryFile('w+', suffix='.scr', delete=False, encoding='utf-8-sig') as file:
        file.write(script)
        file.close() # On Windows file has to be closed before being opened again
        subprocess.run(['accoreconsole.exe', '/s', file.name], capture_output=not verbose)

class Program:
    '''Wrapper to generate AutoCAD script

    Each method corresponds to an AutoCAD command of the same name, except when
    such commands conflict with Python keywords, such as `import_` below.
    '''
    def __init__(self, s=[]):
        self.p = PopenSpawn('accoreconsole.exe', encoding='utf-16-le')
        self._return()
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
        return self._exec(f'open "{path}"')
    def to_dxf(self, path:str=None):
        path = '' if path is None else f'"{path}"'
        return self._append(f'SAVEAS DXF 16 {path}\n')
    def stlout(self, path:str):
        return self._append(f'STLOUT all\n\n\n"{path}"\n(command)\n')
    def erase(self):
        return self._append('ERASE all\n\n')
    def purge(self):
        return self._append(f'-PURGE all * n\n')
    def terminate(self):
        self.p.kill(signal.SIGTERM)
        self.terminated = True
    def _return(self, command=''):
        command = command.split(' ')[0]
        ok = f'Command: {command}.*Command:\r\n' if command else 'Command:\r\n'
        error = '\**MessageBox.*'
        status = self.p.expect([ok, error])
        if status == 0:
            print(self.p.before)
            print(self.p.after)
        if status == 1:
            raise(RuntimeError('\n' + self.p.after))
        return self
    def _exec(self, command):
        '''Send command to AutoCAD for execution'''
        assert not self.terminated, 'Program has already been terminated'
        with tempfile.NamedTemporaryFile('w+', suffix='.scr', delete=False, encoding='utf-8-sig') as file:
            file.write(command)
            file.close() # On Windows file has to be closed before being opened again
            self.p.sendline(f'script {file.name}') # Go the long way to send utf-8 strings to AutoCAD
            return self._return(command)
