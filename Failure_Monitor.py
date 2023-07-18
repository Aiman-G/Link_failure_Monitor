import os # for file paths and svaing csv files
import pandas as pd
import json 
import csv
import datetime

from operator import attrgetter
from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub



class SimpleMonitor13(simple_switch_13.SimpleSwitch13):
    
    link_state_dict ={}
    # we need to start collect failure data from time a datapath registred
    Link_failure_data_path = './my_ryu_apps/monitor_data/failure_data'
    the_datapath_id = ''
    failure_data_file_name =''
    
    def __init__(self, *args, **kwargs):
        super(SimpleMonitor13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath

                # our switch registreation data
                self.link_state_dict['time'] = datetime.datetime.now()
                self.link_state_dict['datapath'] = ev.datapath.id
                self.link_state_dict['registred'] = True
                self.link_state_dict['port_no'] = 66666
                self.link_state_dict['state'] = 4
                self.the_datapath_id = str( ev.datapath.id ) 
                self.failure_data_file_name = os.path.join( self.Link_failure_data_path,'link_failure_dpid_' + self.the_datapath_id + '.csv' )
                self.write_csv(self.link_state_dict, self.failure_data_file_name) 

        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

        
        

        
        
      # *********** Link down Data ***************   
    '''
    From open flow sepcification : 

    /* Current state of the physical port. These are not configurable from
   * the controller.
   */
   enum ofp_port_state {
   OFPPS_LINK_DOWN = 1 << 0, /* No physical link present. */
   FPPS_BLOCKED = 1 << 1, /* Port is blocked */
    OFPPS_LIVE = 1 << 2, /* Live for Fast Failover Group. */
     };

     the output of the folloing function when a link goes down, 
     example for link down :
     mininet> sh  ifconfig s1-eth2 down

     After this command the link goes down on two connnected ports:
     OFPPortStatus received: reason=MODIFY desc=OFPPort(port_no=2,hw_addr='5a:b2:00:89:a2:9a',name=b's1-eth2',config=0,state=0,curr=2112,advertised=0,supported=0,peer=0,curr_speed=10000000,max_speed=0)
     OFPPortStatus received: reason=MODIFY desc=OFPPort(port_no=2,hw_addr='5a:b2:00:89:a2:9a',name=b's1-eth2',config=1,state=1,curr=2112,advertised=0,supported=0,peer=0,curr_speed=10000000,max_speed=0)
     OFPPortStatus received: reason=MODIFY desc=OFPPort(port_no=3,hw_addr='8e:6b:d0:98:87:eb',name=b's5-eth3',config=0,state=0,curr=2112,advertised=0,supported=0,peer=0,curr_speed=10000000,max_speed=0)
     OFPPortStatus received: reason=MODIFY desc=OFPPort(port_no=3,hw_addr='8e:6b:d0:98:87:eb',name=b's5-eth3',config=0,state=1,curr=2112,advertised=0,supported=0,peer=0,curr_speed=10000000,max_speed=0)

    mininet> sh  ifconfig s1-eth2 up
    OFPPortStatus received: reason=MODIFY desc=OFPPort(port_no=2,hw_addr='5a:b2:00:89:a2:9a',name=b's1-eth2',config=0,state=4,curr=2112,advertised=0,supported=0,peer=0,curr_speed=10000000,max_speed=0)

    
    '''

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto

        if msg.reason == ofp.OFPPR_ADD:
            reason = 'ADD'
        elif msg.reason == ofp.OFPPR_DELETE:
            reason = 'DELETE'
        elif msg.reason == ofp.OFPPR_MODIFY:
            reason = 'MODIFY'
            _datapath_id = msg.datapath.id
            
            # our switch link failure data
            self.link_state_dict['time'] = datetime.datetime.now()
            self.link_state_dict['datapath'] = _datapath_id
            self.link_state_dict['registred'] = False
            self.link_state_dict['port_no'] = msg.desc.port_no
            self.link_state_dict['state'] = msg.desc.state
            self.the_datapath_id = str( _datapath_id ) 
            self.failure_data_file_name = os.path.join( self.Link_failure_data_path,'link_failure_dpid_' + self.the_datapath_id + '.csv' )
            self.write_csv(self.link_state_dict, self.failure_data_file_name) 
            
            print ("### switch  NO: ###", msg.datapath.id , "|port:" , msg.desc.port_no, "|State is:", msg.desc.state)
        else:
            reason = 'unknown'

        self.logger.debug('OFPPortStatus received: reason=%s desc=%s',
                      reason, msg.desc)
        #print("@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        #print ("what is desc:", type(msg.desc) )
        # desc is a class
        # if the port is dwon( due link failure), msg.desc.state of the both ends port will go from 0 to 1. As shown in the exmple above the this function
        #  
       # print ("### switch  NO: ###", msg.datapath.id , "|port:" , msg.desc.port_no, "|State is:", msg.desc.state)
        #print("@@@ state @@@", msg.desc.state)
        
# *************************************************

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)


       

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         '
                         'in-port  eth-dst           '
                         'out-port packets  bytes')
        self.logger.info('---------------- '
                         '-------- ----------------- '
                         '-------- -------- --------')
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
            self.logger.info('%016x %8x %17s %8x %8d %8d',
                             ev.msg.datapath.id,
                             stat.match['in_port'], stat.match['eth_dst'],
                             stat.instructions[0].actions[0].port,
                             stat.packet_count, stat.byte_count)

        # *********** Flow Statistics Data ***************
    

        """ path = './my_ryu_apps/monitor_data'
        str_datapath_id = str( ev.msg.datapath.id ) 
        output_file_name = os.path.join( path,'flow_stats_dpid_' + str_datapath_id + '.csv' ) # we will write a independent file for each datapath
        # note : body in ev.msg.body is a list of namedTuples. so to get to the named tuple use the list index frst
        
        for element in body:

            print ("element in flow stats", element )
            flow_stats_dict = {}
            flow_stats_dict['datapath'] = ev.msg.datapath.id

            #print ("element as dict", element._asdict())
            flow_stats_dict_temporary = {}
            flow_stats_dict_temporary = element._asdict() # _asdict() method is a builtin method to convert namedtuples to dictionaries.
            flow_stats_dict = {**flow_stats_dict, **flow_stats_dict_temporary} # merge the temporory dictionry with stats dict, to add datapath first
            #port_stats_dict['port_no'] = hex( port_stats_dict['port_no'] ) # if we want prot numbers in hexidecimal 
            self.write_csv(flow_stats_dict, output_file_name)   """

           
           # *************************************************

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.logger.info('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)

          
          
          
            #port_stats_keys =['datapath' ,'port_no', 'rx_packets', 'tx_packets','rx_bytes','tx_bytes',
          #        'rx_dropped','tx_dropped',
          #        'rx_errors','tx_errors', 'rx_frame_err' ,'rx_over_err','rx_crc_err',
          #        'collisions','duration_sec','duration_nsec']


        # *********** Port statistics Data ************
        path = './my_ryu_apps/monitor_data'
        str_datapath_id = str( ev.msg.datapath.id ) 
        output_file_name = os.path.join( path,'port_stats_dpid_' + str_datapath_id + '.csv' ) # we will write a independent file for each datapath
        # note : body in ev.msg.body is a list of namedTuples. so to get to the named tuple use the list index frst
        for element in body:

            port_stats_dict = {}
            #add time stamp
            port_stats_dict['time'] = datetime.datetime.now()
            port_stats_dict['datapath'] = ev.msg.datapath.id
            

            #print ("element as dict", element._asdict())
            port_stats_dict_temporary = {}
            port_stats_dict_temporary = element._asdict() # _asdict() method is a builtin method to convert namedtuples to dictionaaries.
            port_stats_dict = {**port_stats_dict, **port_stats_dict_temporary} # merge the temporory dictionry with stats dict, to add datapath first
            #port_stats_dict['port_no'] = hex( port_stats_dict['port_no'] ) # if we want prot numbers in hexidecimal 
            self.write_csv(port_stats_dict, output_file_name)  
                         
            
    @staticmethod
    def write_csv(data_dict,output_file_name):

        if os.path.isfile(output_file_name) ==  False : # if file does not exists 
            
            with open(output_file_name, 'w') as outfile:
                writer = csv.writer(outfile) # open file for wiriting ( wriing the headers (column names))
                writer.writerow(list(data_dict.keys())) # add headers

        # open for appending rows , if we want to wirte the updated statistcs of each switch,
        # we can use 'w', instead of 'a'. 
        with open(output_file_name, 'a') as outfile: 
            writer = csv.DictWriter(outfile, fieldnames = data_dict.keys())
            writer.writerow(data_dict)



