from pexpect.popen_spawn import PopenSpawn
import signal

def run_script(script:str, verbose=True):
    '''Excecute a series of AutoCAD commands in a subprocess

    Requires accoreconsole.exe to be in PATH'''
    # It is important to use utf-8-sig not utf-8 on Windows so that Unicode file names are correctly loaded
    with tempfile.NamedTemporaryFile('w+', suffix='.scr', delete=False, encoding='utf-8-sig') as file:
        file.write(script)
        file.close() # On Windows file has to be closed before being opened again
        subprocess.run(['accoreconsole.exe', '/s', file.name], capture_output=not verbose)

class Command:
    '''Wrapper to generate AutoCAD script

    Each method corresponds to an AutoCAD command of the same name, except when
    such commands conflict with Python keywords, such as `import_` below.
    '''
    def __init__(self, s=[]):
        self.s = s
    def __enter__(self):
        self.process = PopenSpawn('accoreconsole.exe', encoding='utf-16-le')
        return self
    def __exit__(self, *_):
        self.exec(verbose=True)
        self.process.kill(signal.SIGTERM)
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
        return self._append(f'OPEN "{path}"\n')
    def to_dxf(self, path:str=None):
        path = '' if path is None else f'"{path}"'
        return self._append(f'SAVEAS DXF 16 {path}\n')
    def stlout(self, path:str):
        return self._append(f'STLOUT all\n\n\n"{path}"\n(command)\n')
    def erase(self):
        return self._append('ERASE all\n\n')
    def purge(self):
        return self._append(f'-PURGE all * n\n')
    def exec(self, verbose=True):
        '''Execute underlying script'''
        s, self.s = self.s, ''
        for line in self.s:
            self.process.send(line)
            i = self.expect(['Command:\r\n', 'HELP\r\n\r\n'])
            print(self.process.before)
