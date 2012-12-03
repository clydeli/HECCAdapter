#!/usr/bin/env python

import os
import pyinotify
import shutil
import stat
import subprocess
import sys

#
# Limitations:
#   * Config files have to be copied to the config folder before project files
#     are copied to the job queue folder.
#

VISTRAILS_SCRIPT_PATH = '/home/owenchu/architecture/vistrails-src-2.0.1-5e35e2b83b90/scripts/run_vistrails_batch_xvfb.sh'
VISTRAILS_OUTPUT_PATH = '/home/owenchu/public_html/vistrails-output'
VISTRAILS_WEB_OUTPUT_PATH = 'http://ok.freya.cc/~owenchu/vistrails-output'

#WORKFLOW = {
#    'offscreen.vt': 'offscreen',
#    'brain_vistrail.vt': 'brain',
#    'head.vt': 'aliases',
#    'triangle_area.vt': 'Surface Area with Map',
#    'spx.vt': 'contour',
#    'protein_visualization.vt': 'Protein Visualization'
#}

class Scheduler:
    def __init__(self, queue_path, config_path, running_path,
                 done_path, result_path):
        self.queue_path = queue_path
        self.handler = self.Handler(queue_path=queue_path,
                                    config_path=config_path,
                                    running_path=running_path,
                                    done_path=done_path,
                                    result_path=result_path)

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
        def my_init(self, queue_path, config_path, running_path,
                    done_path, result_path):
            self.queue_path = queue_path
            self.config_path = config_path
            self.running_path = running_path
            self.done_path = done_path
            self.result_path = result_path

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

            self.result_filepath = os.path.join(self.result_path,
                                                self.project_name(filename) + '.txt')
            Scheduler.log('Project: ' + self.result_filepath)

            workflow = self.workflow_for(filename)
            Scheduler.log('Workflow: ' + workflow)

            cmd_args = [VISTRAILS_SCRIPT_PATH, running_filepath, workflow,
                        VISTRAILS_OUTPUT_PATH]
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
                try:
                    f = open(self.result_filepath, "a")
                    try:
                        _, filename = os.path.split(event.pathname)
                        f.write(VISTRAILS_WEB_OUTPUT_PATH + '/' + filename + '\n')
                    finally:
                        f.close()
                except IOError:
                    pass

        def workflow_for(self, vistrails_project_filename):
            filename, extention = os.path.splitext(vistrails_project_filename)
            config_filepath = os.path.join(self.config_path, filename + ".cfg")
            workflow = ''

            try:
                f = open(config_filepath, "r")
                try:
                    tokens = f.readline().strip().split('=')
                    if (tokens[0] == 'workflow_name'):
                        workflow = tokens[1]
                finally:
                    f.close()
            except IOError:
                pass

            return workflow

        def project_name(self, vistrails_project_filename):
            return os.path.splitext(vistrails_project_filename)[0]

if __name__ == '__main__':
    if len(sys.argv) < 6:
        print >> sys.stderr, "Command line error: missing argument(s)."
        sys.exit(1)

    def compose_path(path):
        return path if os.path.isabs(path) else os.path.join(os.getcwd(), path)

    # Required arguments
    queue_path = compose_path(sys.argv[1])
    config_path = compose_path(sys.argv[2])
    running_path = compose_path(sys.argv[3])
    done_path = compose_path(sys.argv[4])
    result_path = compose_path(sys.argv[5])

    # Blocks monitoring
    Scheduler(queue_path, config_path, running_path,
              done_path, result_path).run()
