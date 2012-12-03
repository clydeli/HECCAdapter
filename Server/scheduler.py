#!/usr/bin/env python

import os
import pyinotify
import shutil
import stat
import subprocess
import sys

VISTRAILS_SCRIPT_PATH = '/home/owenchu/architecture/vistrails-src-2.0.1-5e35e2b83b90/scripts/run_vistrails_batch_xvfb.sh'
VISTRAILS_OUTPUT_PATH = '/home/owenchu/public_html/vistrails-output'

WORKFLOW = {
    'offscreen.vt': 'offscreen',
    'brain_vistrail.vt': 'brain',
    'head.vt': 'aliases',
    'triangle_area.vt': 'Surface Area with Map',
    'spx.vt': 'contour',
    'protein_visualization.vt': 'Protein Visualization'
}

class Scheduler:
    def __init__(self, queue_path, running_path, done_path):
        self.queue_path = queue_path
        self.handler = self.Handler(queue_path=queue_path,
                                    running_path=running_path,
                                    done_path=done_path)

    def run(self):
        wm = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(wm, self.handler)
        wm.add_watch([self.queue_path, VISTRAILS_OUTPUT_PATH],
                     pyinotify.IN_CLOSE_WRITE|pyinotify.IN_CREATE)
        self.log('Start monitoring %s' % queue_path)
        notifier.loop()

    @staticmethod
    def log(msg):
        print("[Scheduler] " + msg)

    class Handler(pyinotify.ProcessEvent):
        def my_init(self, queue_path, running_path, done_path):
            self.queue_path = queue_path
            self.running_path = running_path
            self.done_path = done_path

        def execute_job(self, job_path):
            Scheduler.log("About to execute job: " + job_path)

            _, filename = os.path.split(job_path)
            running_filepath = os.path.join(self.running_path, filename)

            try:
                Scheduler.log('Removing ' + running_filepath)
                os.unlink(running_filepath)
            except OSError:
                pass

            Scheduler.log('Moving %s to %s' %(job_path, self.running_path))
            os.rename(job_path, running_filepath)

            cmd_args = [VISTRAILS_SCRIPT_PATH, running_filepath,
                        WORKFLOW[filename], VISTRAILS_OUTPUT_PATH]
            Scheduler.log(' '.join(cmd_args))
            subprocess.call(cmd_args)
            Scheduler.log('Done')

            done_filepath = os.path.join(self.done_path, filename)
            Scheduler.log('Moving %s to %s' %(running_filepath, self.done_path))
            os.rename(running_filepath, done_filepath)

        def process_IN_CLOSE(self, event):
            if event.pathname.startswith(self.queue_path):
                self.execute_job(event.pathname)

        def process_IN_CREATE(self, event):
            if event.pathname.startswith(VISTRAILS_OUTPUT_PATH):
                Scheduler.log('chmod 644 ' + event.pathname)
                os.chmod(event.pathname,
                         stat.S_IRUSR|stat.S_IWUSR|stat.S_IRGRP|stat.S_IROTH)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print >> sys.stderr, "Command line error: missing argument(s)."
        sys.exit(1)

    # Required arguments
    queue_path = sys.argv[1]
    running_path = sys.argv[2]
    done_path = sys.argv[3]

    # Blocks monitoring
    Scheduler(queue_path, running_path, done_path).run()
