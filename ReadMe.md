# Gst-Whale
A project which reads GST_DEBUG_FILE logs and visualize the trace logs for debugging and optimization. 

## Debug Visualizer
The goal is to see which caps are being negotiated and see which are accepted / rejected for debugging purposes, and see which element pads are linked.

- Run example pipeline to get log file with caps negotiation events
```
GST_DEBUG_FILE=caps.log GST_DEBUG="GST_PADS:5,GST_CAPS:5" gst-launch-1.0 videotestsrc ! video/x-raw,format=RGB,width=320,height=240 ! videoconvert ! videoscale ! video/x-raw,format=I420,width=640,height=480 ! fakesink
```


## Trace Visualizer
The goal is to visualize values from gst-shark tracers for runtime analysis

- Install gst-shark tracers in system 
- Run example pipeline to get gst-shark tracer logs
```
GST_DEBUG_FILE=shark.log GST_DEBUG="GST_TRACER:7" GST_TRACERS="proctime" gst-launch-1.0 videotestsrc ! video/x-raw,format=RGB,width=320,height=240 ! videoconvert ! videoscale ! video/x-raw,format=I420,width=640,height=480 ! fakesink
```