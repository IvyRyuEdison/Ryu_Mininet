# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from operator import attrgetter
#from os import system
import os
#import time
#from ryu.app import simple_switch_13
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from ryu.ofproto import ofproto_v1_3

N = 10
mat1 = [-1 for i in range(N)]
mat2 = [0 for i in range(N) ]
#time0= 0

os.system('echo "" >log')
#os.system('echo "" >time')
class SimpleMonitor13(app_manager.RyuApp):

    def __init__(self, *args, **kwargs):
        super(SimpleMonitor13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

    def delete_flows_2(self, datapath):
        self.logger.info('delete')
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(in_port=1, eth_dst='00:00:00:00:00:02')
        #match = parser.OFPMatch()

        mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE,
                                out_group=ofproto.OFPG_ANY, out_port = ofproto.OFPP_ANY, match=match
                                )
        self.logger.info('finish delete')
        datapath.send_msg(mod)    


    def add_flows_2(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(in_port=1, eth_dst='00:00:00:00:00:02')
        actions = [parser.OFPActionOutput(2)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=1, match=match, instructions=inst)
        datapath.send_msg(mod)




    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(0.5)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # req = parser.OFPFlowStatsRequest(datapath)
        # datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    # @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    # def _flow_stats_reply_handler(self, ev):
    #     body = ev.msg.body

    #     self.logger.info('datapath         '
    #                      'in-port  eth-dst           '
    #                      'out-port packets  bytes')
    #     self.logger.info('---------------- '
    #                      '-------- ----------------- '
    #                      '-------- -------- --------')
    #     for stat in sorted([flow for flow in body if flow.priority == 1],
    #                        key=lambda flow: (flow.match['in_port'],
    #                                          flow.match['eth_dst'])):
    #         self.logger.info('%016x %8x %17s %8x %8d %8d',
    #                          ev.msg.datapath.id,
    #                          stat.match['in_port'], stat.match['eth_dst'],
    #                          stat.instructions[0].actions[0].port,
    #                          stat.packet_count, stat.byte_count)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        datapath = ev.msg.datapath

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
            if stat.port_no > 1000:
                continue
            if mat1[stat.port_no] > 0:
                #print type(stat.rx_bytes)
                #print type(stat.port_no)
                mat2[stat.port_no] = stat.rx_bytes + stat.tx_bytes - mat1[stat.port_no]
            mat1[stat.port_no] = stat.rx_bytes + stat.tx_bytes
            self.logger.info('mat1[%s] : %s', stat.port_no, mat2[stat.port_no])

            #os.system('echo "%s:%s" >> log' %(2, mat2[2]))
        # global time0
        # time1=time.time()-time0
        # time0=time.time()
        # self.logger.info('%s',time1)

        #os.system('echo "%s:%s %s" >> log' %(2, mat2[2],time1))
        os.system('echo "%s" >> log' %(mat2[2]))
        #os.system('echo "%s" >> time' %(time1))


        flag=1
        if mat2[2]-45500>0:
            if mat2[2]-54500>0:
                flag=0
            else:
                flag=1
        # flag=input("delete:0 add:1")
        # if mat2[2]-5000>0:
        #     flag=0
        # else:
        #     flag=1

        flag = int(flag)
        self.logger.info('flag = %s',flag)
        if flag:
            self.add_flows_2(datapath)
        else:
            self.delete_flows_2(datapath)

