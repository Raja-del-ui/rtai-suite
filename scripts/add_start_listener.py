import pathlib

content = pathlib.Path('rtai_core/gui/c2_gui.py').read_text(encoding='utf-8')

old = '''    def create_analyze_section(self):'''

new = '''    def start_listener(self):
        self.set_running(True)

        cmd = [
            sys.executable, '-m', 'rtai_core.gui.c2_gui', 'listener',
            '--host', self.listener_host.text().strip(),
            '--port', str(self.listener_port.value()),
            '--log', self.listener_log.text().strip() or 'beacons.jsonl',
        ]
        if self.listener_tasks.text().strip():
            cmd.extend(['--tasks', self.listener_tasks.text().strip()])
        if self.encode_tasks.isChecked():
            cmd.append('--encode-tasks')

        self.worker = WorkerThread(
            [sys.executable, '-m', 'rtai_core.gui.c2_gui', 'listener'] +
            [arg for arg in [
                '--host', self.listener_host.text().strip(),
                '--port', str(self.listener_port.value()),
                '--log', self.listener_log.text().strip() or 'beacons.jsonl',
                '--tasks', self.listener_tasks.text().strip()] if self.listener_tasks.text().strip() else [] +
                ['--encode-tasks'] if self.encode_tasks.isChecked() else [],
            cwd=str(Path.cwd())
        )

        self.worker.output_signal.connect(self.append_output)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()
        self.set_running(True)

    def create_analyze_section(self):'''

content = pathlib.Path('rtai_core/gui/c2_gui.py').read_text(encoding='utf-8')
content = content.replace(
    '    def create_analyze_section(self):',
    '''    def start_listener(self):
        self.set_running(True)

        cmd = [
            sys.executable, '-m', 'rtai_core.gui.c2_gui', 'listener',
            '--host', self.listener_host.text().strip(),
            '--port', str(self.listener_port.value()),
            '--log', self.listener_log.text().strip() or 'beacons.jsonl',
        ]
        if self.listener_tasks.text().strip():
            cmd.extend(['--tasks', self.listener_tasks.text().strip()])
        if self.encode_tasks.isChecked():
            cmd.append('--encode-tasks')

        self.worker = WorkerThread(
            [sys.executable, '-m', 'rtai_core.gui.c2_gui', 'listener'] +
            [arg for arg in [
                '--host', self.listener_host.text().strip(),
                '--port', str(self.listener_port.value()),
                '--log', self.listener_log.text().strip() or 'beacons.jsonl',
                '--tasks', self.listener_tasks.text().strip()] if self.listener_tasks.text().strip() else [] +
                ['--encode-tasks'] if self.encode_tasks.isChecked() else [],
            cwd=str(Path.cwd())
        )

        self.worker.output_signal.connect(self.append_output)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()
        self.set_running(True)

    def create_analyze_section(self):''')

content = pathlib.Path('rtai_core/gui/c2_gui.py').read_text(encoding='utf-8')
content = content.replace(
    '    def create_analyze_section(self):',
    '''    def start_listener(self):
        self.set_running(True)

        cmd = [
            sys.executable, '-m', 'rtai_core.gui.c2_gui', 'listener',
            '--host', self.listener_host.text().strip(),
            '--port', str(self.listener_port.value()),
            '--log', self.listener_log.text().strip() or 'beacons.jsonl',
        ]
        if self.listener_tasks.text().strip():
            cmd.extend(['--tasks', self.listener_tasks.text().strip()])
        if self.encode_tasks.isChecked():
            cmd.append('--encode-tasks')

        self.worker = WorkerThread(
            [sys.executable, '-m', 'rtai_core.gui.c2_gui', 'listener'] +
            [arg for arg in [
                '--host', self.listener_host.text().strip(),
                '--port', str(self.listener_port.value()),
                '--log', self.listener_log.text().strip() or 'beacons.jsonl',
                '--tasks', self.listener_tasks.text().strip()] if self.listener_tasks.text().strip() else [] +
                ['--encode-tasks'] if self.encode_tasks.isChecked() else [],
            cwd=str(Path.cwd())
        )

        self.worker.output_signal.connect(self.append_output)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()
        self.set_running(True)

    def create_analyze_section(self):''')

pathlib.Path('rtai_core/gui/c2_gui.py').write_text(content, encoding='utf-8')
print('Added start_listener method')