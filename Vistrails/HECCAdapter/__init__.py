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

version = "0.0.2"
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

class HECCAdapter(Module):
    """HECCAdapter is an adapter to HECC"""

    def __init__( self ):
        Module.__init__(self)

    def is_cacheable(self):
        return False

    def compute(self):
        # grab input information from the ports
        #self.vt_filepath = self.forceGetInputFromPort( "vt_filepath" )
        #self.remote_filename = self.forceGetInputFromPort( "remote_filename" )
        #self.username = self.forceGetInputFromPort( "username" )
        #self.password = self.forceGetInputFromPort( "password" )
        #self.sendMode = self.forceGetInputFromPort( "send mode", True )

        print >> sys.stderr," Compute "
        
        # flag the operation as completed
        #self.setResult( "complete flag", True )


###############################################################################

def initialize(*args, **keywords):

    # We'll first create a local alias for the module registry so that
    # we can refer to it in a shorter way.
    basic = core.modules.basic_modules
    reg = core.modules.module_registry.registry
    reg.add_module(HECCAdapter)
    
    global usageWindow
    usageWindow = UsageViewer()
    usageWindow.show()

    #reg.add_input_port(HECCAdapter, "username", basic.String)
    #reg.add_input_port(HECCAdapter, "password", basic.String)
    #reg.add_input_port(HECCAdapter, "vt_filepath", basic.String)
    #reg.add_input_port(HECCAdapter, "remote_filename", basic.String)
    #reg.add_output_port(HECCAdapter, "complete flag", basic.Boolean)


###################

def menu_items():

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


    def send_to_HECC():
        
        # this line prints out the latest workflow name which we can leverage later
        print >> sys.stderr, api.get_available_versions()[1][api.get_available_versions()[0][-1]]

        vt_filepath = api.get_current_controller().get_locator().name
        remote_filename = vt_filepath.split('/')[-1]
        
        # login info
        username = "clydeli"
        password = "JiaRocks"

        # spawn the scp pexpect thread and login
        processID = -1
        spawnLine = "scp " + vt_filepath + " " + username + "@ok.freya.cc:/home/hecc/job_queue/" + remote_filename
        print >> sys.stderr," [scp Module] scp spawning line: (" + spawnLine + ")"
        thePrompt = pexpect.spawn( spawnLine )
        login( thePrompt, password )

    def view_usages():
      usageWindow.show()
      usageWindow.activateWindow()
      usageWindow.raise_()

    lst = []
    lst.append(("Send to HECC", send_to_HECC))
    lst.append(("View Usages", view_usages))
    return tuple(lst)
