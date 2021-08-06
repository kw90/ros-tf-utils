# PoseStamped to TF Rebroadcaster
This ROS node rebroadcasts a PoseStamped topic to a TF coordinate frame.

Run it by copying the config file and configuring it for your environment. Then
for testing simply run the file
`src/pose_to_tf/posestamped_to_tf_rebroadcaster.py` with `Python2.7`.

```zsh
python2.7 src/pose_to_tf/pose_to_tf_rebroadcaster.py --config_file configs/config.yaml
```

:information_source: When using `posestamped_to_tf_rebroadcaster.py`, make sure
that you are using a `PoseStamped` topic. Otherwise, for a `Pose` topic use the
`pose_to_tf_rebroadcaster.py` file.

If all goes well, the following is printed and the new frame should be visible
in RViz.

```
[INFO] [1628243332.120338]: Pose to TF rebroadcaster is now running...
```

:information_source: You can run this node with rqt_ez_publisher to get
a quick-and-dirty GUI to add and move a virtual pose.

## Tests

Run the tests with the following command

```zsh
python2.7 -m pytest pose_to_tf/src/pose_to_tf/test -vv
```
