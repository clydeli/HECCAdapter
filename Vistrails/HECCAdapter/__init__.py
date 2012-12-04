from core.modules.vistrails_module import Module, ModuleError
import core.modules
import core.modules.basic_modules
import core.modules.module_registry
import core.system
import gui.application
from PyQt4 import QtCore, QtGui

import api
import sys
import pexpect
import re
import monitor
import uuid
import time

version = "0.0.3"
name = "HECCAdapter"
identifier = "edu.cmu.nasaproject.vistrails.heccadapter"

class UsageViewer(QtGui.QWidget):
    """UsageViewer shows CPU usage, PBS job statuses, and Filesystem usage"""
    
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Usage Viewer')
        gridLayout = QtGui.QGridLayout()
        self.setLayout(gridLayout)

        self.usage_label = QtGui.QLabel()
        gridLayout.addWidget(self.usage_label, 1, 0)

        self.cpuUsageButton = QtGui.QPushButton('CPU Usage')
        gridLayout.addWidget(self.cpuUsageButton, 0, 0)
        self.connect(self.cpuUsageButton, QtCore.SIGNAL('clicked()'), self.updateCpuView)

        self.pbsUsageButton = QtGui.QPushButton('PBS Usage')
        gridLayout.addWidget(self.pbsUsageButton, 0, 1)
        self.connect(self.pbsUsageButton, QtCore.SIGNAL('clicked()'), self.updatePbsView)

        self.filesystemUsageButton = QtGui.QPushButton('Filesystem Usage')
        gridLayout.addWidget(self.filesystemUsageButton, 0, 2)
        self.connect(self.filesystemUsageButton, QtCore.SIGNAL('clicked()'), self.updateFsView)

    def updateCpuView(self):
        self.usage_label.setText(monitor.get_cpu_use())

    def updatePbsView(self):
        self.usage_label.setText(monitor.get_pbs_jobs())

    def updateFsView(self):
        self.usage_label.setText(monitor.get_filesystem_usage())


class JobStatusViewer(QtGui.QWidget):

    def __init__(self, parent=None):

        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Job Status')
        gridLayout = QtGui.QGridLayout()
        self.setLayout(gridLayout)

        self.usage_label = QtGui.QLabel()
        self.usage_label.setTextFormat(QtCore.Qt.RichText)
        self.usage_label.setOpenExternalLinks(True)
        gridLayout.addWidget(self.usage_label, 1, 0)

    def updateStatus(self):

        # [The LOGIN function is directly copied from remoteLogin package] 
        def login( thePrompt, password ):
            theResult = thePrompt.expect( ['continue connecting',
                                           'assword:',
                                           pexpect.EOF] )

            # check if this is the first time we have tried to login to the server
            if theResult==0:
                print >> sys.stderr," [scpModule] login -- first time fingerprint"
                thePrompt.sendline( 'yes' )
                theResult = thePrompt.expect( ['continue connecting',
                                               'assword:',
                                               pexpect.EOF] )

            # respond to the result after potential fingerprint acceptance
            if theResult==0:
                print >> sys.stderr," [scpModule] login -- sanity failure -- first time fingerprint again"
                raise RuntimeError, "sanity failure -- fingerprint double check"
            elif theResult==2:
                print >> sys.stderr," [scpModule] login -- received EOF signal"
                raise RuntimeError, "login failure -- early EOF received"

            # otherwise process the password prompt
            elif theResult==1:
                print >> sys.stderr," [scpModule] login -- received password prompt"
                thePrompt.sendline( password )
                theResult = thePrompt.expect( ['assword:',pexpect.EOF] )

                # check the responses
                if theResult==0:
                    print >> sys.stderr," [scpModule] login -- failure denied password"
                    raise RuntimeError,"login failure -- denied username/password"
                else:
                    print >> sys.stderr," [scpModule] successful login..."

        self.usage_label.setText("Loading...")

        # login info
        username = loginWindow.username
        password = loginWindow.password

        # spawn the scp pexpect thread and login
        spawnLine_queue = "ssh " + username + "@ok.freya.cc \"" + "find /home/hecc/job_queue -type f | grep '/"+username+"_'" + "\""
        spawnLine_running = "ssh " + username + "@ok.freya.cc \"" + "find /home/hecc/running -type f | grep '/"+username+"_'" + "\""
        spawnLine_results = "ssh " + username + "@ok.freya.cc \"" + "find /home/hecc/results -type f | grep '/"+username+"_'" + "\""
        thePrompt_queue = pexpect.spawn( spawnLine_queue )
        thePrompt_running = pexpect.spawn( spawnLine_running )
        thePrompt_results = pexpect.spawn( spawnLine_results )
        login( thePrompt_queue, password )
        login( thePrompt_running, password )
        login( thePrompt_results, password )
        in_queue_jobs = thePrompt_queue.before.replace("/home/hecc/job_queue/", "")
        running_jobs = thePrompt_running.before.replace("/home/hecc/running/", "")
        done_results = thePrompt_results.before.split('\n')

        displayText = "In Queue:<br>"+in_queue_jobs+"<br>Running:<br>"+running_jobs+"<br>Done:<br>"
        for result in done_results[1:-1]:
            displayText += "[Job] "+result.replace("/home/hecc/results/", "")[:-5]+"<br>"
            spawnLine_result = "ssh " + username + "@ok.freya.cc \"" + "cat "+result[:-1] + "\""
            thePrompt_result = pexpect.spawn( spawnLine_result )
            login( thePrompt_result, password )
            displayText += '<a href="%s">%s</a><br>' %(thePrompt_result.before[:-1], thePrompt_result.before[:-1])
        
        self.usage_label.setText(displayText)


class LoginViewer(QtGui.QWidget):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Login Viewer')
        gridLayout = QtGui.QGridLayout()
        self.setLayout(gridLayout)

        self.usernameLabel = QtGui.QLabel('User Name')
        gridLayout.addWidget(self.usernameLabel, 0, 0)
        self.usernameEdit = QtGui.QLineEdit()
        gridLayout.addWidget(self.usernameEdit, 0, 1)

        self.passwordLabel = QtGui.QLabel('Password')
        gridLayout.addWidget(self.passwordLabel, 1, 0)
        self.passwordEdit = QtGui.QLineEdit()
        self.passwordEdit.setEchoMode(QtGui.QLineEdit.Password)
        gridLayout.addWidget(self.passwordEdit, 1, 1)

        self.loginButton = QtGui.QPushButton('Login')
        gridLayout.addWidget(self.loginButton, 2, 1)
        self.connect(self.loginButton, QtCore.SIGNAL('clicked()'), self.save)

    def save(self):
        self.username = str(self.usernameEdit.text())
        self.password = str(self.passwordEdit.text())

        # stupid simulation
        time.sleep(3)
        rsaWindow.generate_rsa()
        rsaWindow.show()
        rsaWindow.activateWindow()
        rsaWindow.raise_()

        self.hide()


class RSAViewer(QtGui.QWidget):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('RSA Token Input')
        gridLayout = QtGui.QGridLayout()
        self.setLayout(gridLayout)

        self.rsaLabel = QtGui.QLabel('Input RSA Token')
        gridLayout.addWidget(self.rsaLabel, 0, 0)
        self.rsaEdit = QtGui.QLineEdit()
        gridLayout.addWidget(self.rsaEdit, 1, 0)

        self.okButton = QtGui.QPushButton('OK')
        gridLayout.addWidget(self.okButton, 2, 0)
        self.connect(self.okButton, QtCore.SIGNAL('clicked()'), self.check)

    def generate_rsa(self):
        self.rsaEdit.setText(str(uuid.uuid4())[0:8])

    def check(self):
        self.hide()


class SendViewer(QtGui.QWidget):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Send to HECC Settings')
        gridLayout = QtGui.QGridLayout()
        self.setLayout(gridLayout)

        self.emailLabel = QtGui.QLabel('Notification Email')
        gridLayout.addWidget(self.emailLabel, 0, 0)
        self.emailEdit = QtGui.QLineEdit()
        gridLayout.addWidget(self.emailEdit, 0, 1)

        self.ncpusLabel = QtGui.QLabel('Number of CPUs')
        gridLayout.addWidget(self.ncpusLabel, 1, 0)
        self.ncpusEdit = QtGui.QLineEdit()
        self.ncpusEdit.setText("32")
        gridLayout.addWidget(self.ncpusEdit, 1, 1)

        self.prefLabel = QtGui.QLabel('Preference')
        gridLayout.addWidget(self.prefLabel, 2, 0)
        self.prefCombo = QtGui.QComboBox()
        self.prefCombo.addItem("Performance", "performance")
        self.prefCombo.addItem("Cost", "cost")
        self.prefCombo.addItem("Manual", "manual")
        gridLayout.addWidget(self.prefCombo, 2, 1)

        self.nodeLabel = QtGui.QLabel('Node Type')
        gridLayout.addWidget(self.nodeLabel, 3, 0)
        self.nodeCombo = QtGui.QComboBox()
        self.nodeCombo.addItem("Sandy Bridge", "san")
        self.nodeCombo.addItem("Westmere", "wes")
        self.nodeCombo.addItem("Nehalem", "neh")
        self.nodeCombo.addItem("Harpertown", "har")
        gridLayout.addWidget(self.nodeCombo, 3, 1)

        self.selectLabel = QtGui.QLabel('Number of Nodes')
        gridLayout.addWidget(self.selectLabel, 4, 0)
        self.selectEdit = QtGui.QLineEdit()
        self.selectEdit.setText("2")
        gridLayout.addWidget(self.selectEdit, 4, 1)


        self.sendButton = QtGui.QPushButton('Send to HECC')
        gridLayout.addWidget(self.sendButton, 5, 1)
        self.connect(self.sendButton, QtCore.SIGNAL('clicked()'), self.send)


    def send(self):
    
        # [The LOGIN function is directly copied from remoteLogin package] 
        # LOGIN -- handle the login with all its odd 'expected' cases of
        # failure/success.  returns a boolean indicating the ability to
        # login to the prompt with the given username and password
        def login( thePrompt, password ):
            theResult = thePrompt.expect( ['continue connecting',
                                           'assword:',
                                           pexpect.EOF] )

            # check if this is the first time we have tried to login to the server
            if theResult==0:
                print >> sys.stderr," [scpModule] login -- first time fingerprint"
                thePrompt.sendline( 'yes' )
                theResult = thePrompt.expect( ['continue connecting',
                                               'assword:',
                                               pexpect.EOF] )

            # respond to the result after potential fingerprint acceptance
            if theResult==0:
                print >> sys.stderr," [scpModule] login -- sanity failure -- first time fingerprint again"
                raise RuntimeError, "sanity failure -- fingerprint double check"
            elif theResult==2:
                print >> sys.stderr," [scpModule] login -- received EOF signal"
                raise RuntimeError, "login failure -- early EOF received"

            # otherwise process the password prompt
            elif theResult==1:
                print >> sys.stderr," [scpModule] login -- received password prompt"
                thePrompt.sendline( password )
                theResult = thePrompt.expect( ['assword:',pexpect.EOF] )

                # check the responses
                if theResult==0:
                    print >> sys.stderr," [scpModule] login -- failure denied password"
                    raise RuntimeError,"login failure -- denied username/password"
                else:
                    print >> sys.stderr," [scpModule] successful login..."

    
        # this line prints out the latest workflow name which we can leverage later
        workflow_name = api.get_available_versions()[1][api.get_available_versions()[0][-1]]
        
        # login info
        username = loginWindow.username
        password = loginWindow.password
        
        vt_filepath = api.get_current_controller().get_locator().name
        remote_filename = username + "_" + str(uuid.uuid4()) + "_" + vt_filepath.split('/')[-1][:-3]

        # spawn the scp pexpect thread and login
        config_text = "email: "+str(self.emailEdit.text())+"\\nworkflow_name: "+str(workflow_name)+"\\nscheduling: "
        config_text += "\\n    type: "+str(self.prefCombo.itemData(self.prefCombo.currentIndex()).toString())
        config_text += "\\n    ncpus: "+str(self.ncpusEdit.text())
        config_text += "\\n    node: "+str(self.nodeCombo.itemData(self.nodeCombo.currentIndex()).toString())
        config_text += "\\n    select: "+str(self.selectEdit.text())
        #print >> sys.stderr, config_text

        spawnLine_cfg = "ssh " + username + "@ok.freya.cc \"" + "echo -ne '"+config_text+"' >> /home/hecc/config/"+remote_filename+".yml" + "\""
        #print >> sys.stderr, spawnLine_cfg
        thePrompt_cfg = pexpect.spawn( spawnLine_cfg )
        login( thePrompt_cfg, password )

        spawnLine = "scp " + vt_filepath + " " + username + "@ok.freya.cc:/home/hecc/job_queue/" + remote_filename + ".vt"
        #print >> sys.stderr," [scp Module] scp spawning line: (" + spawnLine + ")"
        thePrompt = pexpect.spawn( spawnLine )
        login( thePrompt, password )

        self.hide()
    


class HECCAdapter(Module):
    """HECCAdapter is an adapter to HECC"""

    def __init__( self ):
        Module.__init__(self)

    def is_cacheable(self):
        return False

    def compute(self):
        print >> sys.stderr," Compute "
        # grab input information from the ports
        #self.vt_filepath = self.forceGetInputFromPort( "vt_filepath" )
        #self.remote_filename = self.forceGetInputFromPort( "remote_filename" )
        #self.username = self.forceGetInputFromPort( "username" )
        #self.password = self.forceGetInputFromPort( "password" )
        #self.sendMode = self.forceGetInputFromPort( "send mode", True )

        # flag the operation as completed
        #self.setResult( "complete flag", True )

###############################################################################

def initialize(*args, **keywords):

    # We'll first create a local alias for the module registry so that
    # we can refer to it in a shorter way.
    basic = core.modules.basic_modules
    reg = core.modules.module_registry.registry
    reg.add_module(HECCAdapter)
    
    global loginWindow, usageWindow, jobstatusWindow, rsaWindow, sendWindow
    loginWindow = LoginViewer()
    usageWindow = UsageViewer()
    jobstatusWindow = JobStatusViewer()
    rsaWindow = RSAViewer()
    sendWindow = SendViewer()

###################

def menu_items():

    def view_usages():
        usageWindow.show()
        usageWindow.activateWindow()
        usageWindow.raise_()

    def view_jobstatus():
        jobstatusWindow.show()
        jobstatusWindow.activateWindow()
        jobstatusWindow.raise_()
        jobstatusWindow.updateStatus()

    def log_on_HECC():
        loginWindow.show()
        loginWindow.activateWindow()
        loginWindow.raise_()

    def send_to_HECC():
        sendWindow.show()
        sendWindow.activateWindow()
        sendWindow.raise_()

    lst = []
    lst.append(("Log on HECC", log_on_HECC))
    lst.append(("Send to HECC", send_to_HECC))
    lst.append(("View HECC Usages", view_usages))
    lst.append(("View Job Status", view_jobstatus))
    return tuple(lst)
