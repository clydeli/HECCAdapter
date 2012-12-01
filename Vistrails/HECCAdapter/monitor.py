'''
Created on Nov 29, 2012

@author: normanxin
'''

def get_page(url):
    import urllib
    response=urllib.urlopen(url)
    page=response.read() 
    return page

def get_cpu_use():
    page=get_page("http://www.nas.nasa.gov/monitoring/hud/realtime/pleiadespanel1.html")
    return page

def get_pbs_jobs():
    page=get_page("http://www.nas.nasa.gov/monitoring/hud/realtime/pleiadespanel2.html")
    return page

def get_filesystem_usage():
    page=get_page("http://www.nas.nasa.gov/monitoring/hud/realtime/pleiadespanel3.html")
    return page

