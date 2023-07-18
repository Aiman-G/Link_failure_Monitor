# Link_failure_Monitor



This Ryu application  will record the switch statistics and the link failure.
It will record the link states and the switch statistics for every switch separately( each switch will have a csv file ) . The statistics in a folder and the failure information in another folder.
Read the OpenFlow specification to understand the recorded data:


'''
    From open flow sepcification : 

    /* Current state of the physical port. These are not configurable fromthe controller. 
   enum ofp_port_state {
   OFPPS_LINK_DOWN = 1 << 0, // No physical link present. 
   FPPS_BLOCKED = 1 << 1, // Port is blocked 
    OFPPS_LIVE = 1 << 2, // Live for Fast Failover Group. 
     };

     the output of the folloing function when a link goes down, 
     example for link down :
     mininet> sh  ifconfig s1-eth2 down

     After this command the link goes down on two connnected ports:
     OFPPortStatus received: reason=MODIFY desc=OFPPort(port_no=2,hw_addr='5a:b2:00:89:a2:9a',name=b's1-eth2',config=0,state=0,curr=2112,advertised=0,supported=0,peer=0,curr_speed=10000000,max_speed=0)
     OFPPortStatus received: reason=MODIFY desc=OFPPort(port_no=2,hw_addr='5a:b2:00:89:a2:9a',name=b's1-eth2',config=1,state=1,curr=2112,advertised=0,supported=0,peer=0,curr_speed=10000000,max_speed=0)
     OFPPortStatus received: reason=MODIFY desc=OFPPort(port_no=3,hw_addr='8e:6b:d0:98:87:eb',name=b's5-eth3',config=0,state=0,curr=2112,advertised=0,supported=0,peer=0,curr_speed=10000000,max_speed=0)
     OFPPortStatus received: reason=MODIFY desc=OFPPort(port_no=3,hw_addr='8e:6b:d0:98:87:eb',name=b's5-eth3',config=0,state=1,curr=2112,advertised=0,supported=0,peer=0,curr_speed=10000000,max_speed=0)

     */

   
