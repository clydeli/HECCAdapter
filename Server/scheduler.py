#!/usr/bin/env python

import os
import pyinotify
import shutil
import smtplib
import stat
import string
import subprocess
import sys
import yaml

#
# Limitations:
#   * Config files have to be copied to the config folder before project files
#     are copied to the job queue folder.
#

SETTING = yaml.load(open('setting.yml', 'r'))

class Scheduler:
    def __init__(self, paths):
        self.paths = paths
        self.handler = self.Handler(paths=paths)

    def run(self):
        wm = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(wm, self.handler)
        wm.add_watch([self.paths['queue'], SETTING['vistrails']['output_path']],
                     pyinotify.IN_CLOSE_WRITE|pyinotify.IN_CREATE)
        self.log('Start monitoring %s' % self.paths['queue'])
        notifier.loop()

    @staticmethod
    def log(msg):
        print("[Scheduler] " + msg)

    class Handler(pyinotify.ProcessEvent):
        def my_init(self, paths):
            self.paths = paths
            self.notified = {}

        def execute_job(self, job_path):
            Scheduler.log("About to execute job: " + job_path)

            _, filename = os.path.split(job_path)
            self.running_project = self.project_name(filename)

            running_filepath = os.path.join(self.paths['running'], filename)

            # Remove old project file with the same name
            try:
                Scheduler.log('Removing ' + running_filepath)
                os.unlink(running_filepath)
            except OSError:
                pass

            # Move the job to 'running' folder
            Scheduler.log('Moving %s to %s' %(job_path, self.paths['running']))
            os.rename(job_path, running_filepath)

            self.result_filepath = os.path.join(self.paths['result'],
                                        self.project_name(filename) + '.txt')
            Scheduler.log('Project: ' + self.result_filepath)

            workflow = self.workflow_for(filename)
            Scheduler.log('Workflow: ' + workflow)

            # Run VisTrails
            cmd_args = [SETTING['vistrails']['script_path'],
                        running_filepath, workflow,
                        SETTING['vistrails']['output_path']]
            Scheduler.log(' '.join(cmd_args))
            subprocess.call(cmd_args)
            Scheduler.log('Done')

            # Move the job to 'done' folder
            done_filepath = os.path.join(self.paths['done'], filename)
            Scheduler.log('Moving %s to %s' % (running_filepath,
                                               self.paths['done']))
            os.rename(running_filepath, done_filepath)

            # Trigger notification
            self.notified[self.running_project] = False

        def process_IN_CLOSE(self, event):
            if event.pathname.startswith(self.paths['queue']):
                self.execute_job(event.pathname)

        def process_IN_CREATE(self, event):
            if event.pathname.startswith(SETTING['vistrails']['output_path']):
                Scheduler.log('chmod 644 ' + event.pathname)
                os.chmod(event.pathname,
                         stat.S_IRUSR|stat.S_IWUSR|stat.S_IRGRP|stat.S_IROTH)
                try:
                    f = open(self.result_filepath, "a")
                    try:
                        _, filename = os.path.split(event.pathname)
                        url = SETTING['vistrails']['web_output_path'] + '/' + filename
                        f.write(url + '\n')

                        if not self.notified[self.running_project]:
                            Scheduler.log('Sending notification for ' + self.running_project)
                            self.send_notification(self.running_project, url)
                            self.notified[self.running_project] = True
                    finally:
                        f.close()
                except IOError:
                    pass

        def workflow_for(self, vistrails_project_filename):
            filename, extention = os.path.splitext(vistrails_project_filename)
            config_filepath = os.path.join(self.paths['config'], filename + ".cfg")
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

        def send_notification(self, vistrails_project_name, url):
            to = 'owen.chu@sv.cmu.edu'
            body = string.join((
                    'From: %s' % SETTING['notification']['sender'],
                    'To: %s' % to,
                    'Subject: [HECC] Your compute job was completed',
                    '',
                    'Your compute job "%s" was completed.' % vistrails_project_name,
                    '',
                    'You can launch VisTrails or go the the following page to check the results:',
                    url
                    ), "\r\n")

            server = smtplib.SMTP(SETTING['notification']['smtp_server'],
                                  SETTING['notification']['smtp_port'])
            server.starttls()
            server.login(SETTING['notification']['sender'],
                         SETTING['notification']['sender_password'])
            server.sendmail(SETTING['notification']['sender'], [to], body)
            server.quit()


def main():
    if len(sys.argv) < 6:
        print >> sys.stderr, "Command line error: missing argument(s)."
        sys.exit(1)

    def compose_path(path):
        return path if os.path.isabs(path) else os.path.join(os.getcwd(), path)

    # Required arguments
    paths = {
        'queue': compose_path(sys.argv[1]),
        'config': compose_path(sys.argv[2]),
        'running': compose_path(sys.argv[3]),
        'done': compose_path(sys.argv[4]),
        'result': compose_path(sys.argv[5])
    }

    # Blocks monitoring
    Scheduler(paths).run()


if __name__ == '__main__':
    main()
