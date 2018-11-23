# gst-simple-sap-player
simple python gstreamer player for playing multicast video and reading the meta data of the video from sap 


# Install requirements
  
    INSTALL GSTREAMER LIBS GOOGLE IT YOURSELF  
    $ source /venv/bin/activate 
    $ pip install -r requirements.txt

# Usage 

create a multicast route 

    sudo route add -net <multcast ip> dev <the device receiving the stream>

then launch the app
  
    ./player.py
