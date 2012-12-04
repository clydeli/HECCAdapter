import urllib
from sgmllib import SGMLParser

class PageParser(SGMLParser):
  def reset(self):
    self.datas=[]
    SGMLParser.reset(self)
  def parse(self,data):
    self.feed(data)
    self.close()
  def handle_data(self,data):
    if not data.isspace(): 
      self.datas.append(data.strip())

class NodeMonitor:
  def __init__(self):
    self.node_stat = {}

  def fetch_page(self, url):
    response = urllib.urlopen(url)
    page = response.read() 
    return page
  
  def parse_page(self, page):
    parser = PageParser()
    parser.parse(page)
    return parser.datas
  
  def fetch_node_stat(self):
    page = self.fetch_page("http://www.nas.nasa.gov/monitoring/hud/realtime/pleiadespanel1.html")
    raw_data = self.parse_page(page)
    self.node_stat = {
      'har_in_use':raw_data[13],
      'har_available':raw_data[15],
      'har_free':raw_data[17],
      'neh_in_use':raw_data[20],
      'neh_available':raw_data[22],
      'neh_free':raw_data[24],
      'san_in_use':raw_data[27],
      'san_available':raw_data[29],
      'san_free':raw_data[31],
      'wes_in_use':raw_data[34],
      'wes_available':raw_data[36],
      'wes_free':raw_data[38],
    }

class NodeScheduler:
  def __init__(self):
    self.node_types = [
      {'model':'san', 'ncpus':16},
      {'model':'wes', 'ncpus':12},
      {'model':'neh', 'ncpus':8},
      {'model':'har', 'ncpus':8}]
    self.node_monitor = NodeMonitor()

  def reserve(self, node_type, num_req_cpus):
    num_available_nodes = int(self.node_monitor.node_stat[node_type['model']+'_available'])  
    model = node_type['model']
    ncpus = node_type['ncpus']
    available_nodes = []
    while(num_req_cpus>0 or num_available_nodes>0):
      if num_req_cpus < ncpus:
        num_select = num_req_cpus 
      else:
        num_select = ncpus
      num_req_cpus -= num_select
      num_available_nodes -= 1
      available_nodes += [{'model':model, 'ncpus':ncpus, 'select':num_select}]
    return (available_nodes, num_req_cpus)

  def schedule(self, mode, num_req_cpus):
    self.node_monitor.fetch_node_stat()
    total_nodes = []
    if mode == 'fastest':
      for t in self.node_types:
        print "!!!!" + str(num_req_cpus)
        if num_req_cpus <= 0:
          break
        available_nodes, num_req_cpus = self.reserve(t, num_req_cpus)
        total_nodes += available_nodes
    elif mode == 'cheapest':
      for t in reversed(self.node_types):
        if num_req_cpus <= 0:
          break
        available_nodes, num_req_cpus = self.reserve(t, num_req_cpus)
        total_nodes.append(available_nodes)
    else:
      return None

    if num_req_cpus <= 0:
      return total_nodes
    else:
      return None

if __name__ == "__main__":
  scheduler = NodeScheduler()
  print scheduler.schedule('fastest', 16)
