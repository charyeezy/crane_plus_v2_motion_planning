#!/usr/bin/env python
###
# File Created: Saturday, January 12th 2019, 11:23:55 am
# Author: Charlene Leong charleneleong84@gmail.com
# Modified By: Charlene Leong
# Last Modified: Wednesday, February 6th 2019, 8:45:47 pm
###

import sys
import rospy
import moveit_commander

from utils.ros import check_rosparams

from modules import BenchmarkSession
from modules import HyperOptSession
from modules import SMACSession
from modules import OpenTunerSession
from modules import SKOptSession
    

def main():
    moveit_commander.roscpp_initialize(sys.argv)
    rospy.init_node('parameter_tuning', anonymous=True)
    check_rosparams()

    mode = rospy.get_param('~mode')
    if(mode in ['default', 'ompl']):
        session = BenchmarkSession()
    elif(mode in ['tpe', 'rand']):
        session = HyperOptSession()
    elif(mode == 'smac'):
        session = SMACSession()
    elif(mode == 'aucbandit'):
        session = OpenTunerSession()
    elif(mode in ['gp', 'rf', 'et', 'gbrt']):
        session = SKOptSession()

    session.run_session()

    moveit_commander.roscpp_shutdown()

if __name__ == '__main__':
    main()