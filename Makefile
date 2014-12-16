CFLAGS = `pkg-config opencv cvblob --libs --cflags`

%: %.cpp
	g++ -O2 $< -o $@ $(CFLAGS) 
