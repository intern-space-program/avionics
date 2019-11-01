#########################################
# PACKETIZER MAKEFILE
#
#
#
#########################################

PLATFORM = PC
DEBUG = NONE

CFLAGS = -D $(PLATFORM) -D $(DEBUG)

a.out: packetizer.o test.o
	g++ packetizer.o test.o

packetizer.o: packetizer.h packetizer.c
	g++ -c packetizer.c $(CFLAGS)

test.o: test.c
	g++ -c test.c

#########################################
# RULES
#########################################
clean:
	rm a.out *.o

# PI:
# 	$(PLATFORM)=PI

# PC:
# 	$(PLATFORM)=PC