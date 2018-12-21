
// Copyright 2018 Charlene Leong (charleneleong84@gmail.com)


#include <ros/ros.h>
#include <moveit/move_group_interface/move_group_interface.h>

int main(int argc, char **argv) {
  ros::init(argc, argv, "resting");
  ros::NodeHandle nh;

  ros::AsyncSpinner spinner(2);
  spinner.start();

  // Set up the arm planning interface
  moveit::planning_interface::MoveGroupInterface arm("arm");
  // Specify end-effector positions in the "base_link" task frame
  arm.setPoseReferenceFrame("base_link");
  //arm.setPlannerId("BiTRRTkConfigDefault"); 
  //arm.setPlannerId("BKPIECEkConfigDefault");  
  arm.setPlannerId("KPIECEkConfigDefault");  

  // Plan a move to the "resting" pose
  arm.setNamedTarget("resting");
  // Execute the move
  ROS_INFO("Moving to resting pose");

  //Execute motion path
  if (!arm.move()) {
    ROS_WARN("Could not move to desired pose");
    return 1;
  }


  ros::shutdown();
  return 0;
}